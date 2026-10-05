"""실제 추론 결과와 주문의 저장/거절 경계를 검증합니다. 외부 서비스는 사용하지 않습니다."""

from decimal import Decimal
from pathlib import Path
import sys
import tempfile
import unittest

from rdflib import Graph, Literal, RDF, XSD

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ontology_practice import advanced_cafe as app


class OntologyApplicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = app.load_data()
        cls.graph = app.prepare(cls.data)

    def copy_data(self):
        data = Graph()
        data += self.data
        return data

    def decisions(self, **kwargs):
        return {row["menu_id"].rsplit("#", 1)[-1]: row for row in app.recommend(self.graph, **kwargs)}

    def test_property_chains_and_restriction_classification(self):
        self.assertNotIn((app.EX.MilkLatte, app.EX.containsAllergen, app.EX.MilkAllergen), self.data)
        self.assertIn((app.EX.MilkLatte, app.EX.containsAllergen, app.EX.MilkAllergen), self.graph)
        self.assertIn((app.EX.OatLatte, app.EX.containsIngredient, app.EX.Coffee), self.graph)
        self.assertIn((app.EX.Coffee, RDF.type, app.EX.CaffeinatedIngredient), self.graph)
        self.assertIn((app.EX.Americano, RDF.type, app.EX.CaffeinatedMenu), self.graph)
        self.assertNotIn((app.EX.SesameCookie, RDF.type, app.EX.CaffeinatedMenu), self.graph)

    def test_inverse_and_region_chain(self):
        self.assertIn((app.EX.BeanSupplier, app.EX.suppliesIngredient, app.EX.Coffee), self.graph)
        self.assertEqual(set(self.graph.objects(app.EX.GangnamStore, app.EX.inRegion)),
                         {app.EX.Gangnam, app.EX.Seoul, app.EX.Korea})

    def test_supplier_impact_is_derived(self):
        rows = app.supplier_impact(self.graph, app.EX.BeanSupplier)
        self.assertEqual({row["menu_id"] for row in rows},
                         {str(app.EX.Americano), str(app.EX.MilkLatte), str(app.EX.OatLatte)})

    def test_recommendation_explains_rejections(self):
        rows = self.decisions()
        self.assertEqual({name for name, row in rows.items() if row["eligible"]}, {"Americano", "OatLatte"})
        self.assertTrue(any(reason.startswith("ALLERGEN:") for reason in rows["MilkLatte"]["reasons"]))
        self.assertTrue(any(reason.startswith("NON_VEGAN:") for reason in rows["MilkLatte"]["reasons"]))
        self.assertTrue(any(reason.startswith("STOCK:") for reason in rows["MatchaLatte"]["reasons"]))

    def test_caffeine_preference_uses_inferred_type(self):
        rows = self.decisions(customer=app.EX.Jisu)
        self.assertTrue(rows["SesameCookie"]["eligible"])
        self.assertFalse(rows["Americano"]["eligible"])
        self.assertTrue(any(reason.startswith("CAFFEINE:") for reason in rows["Americano"]["reasons"]))

    def test_quantity_scales_stock_and_total_price(self):
        rows = self.decisions(quantity=2, budget=10000)
        self.assertTrue(rows["Americano"]["eligible"])
        self.assertFalse(rows["OatLatte"]["eligible"])
        self.assertEqual(rows["OatLatte"]["total_price"], 9000)
        self.assertTrue(any("400g" in reason for reason in rows["OatLatte"]["reasons"]))
        rows = self.decisions(quantity=2)
        self.assertTrue(any(reason.startswith("BUDGET:") for reason in rows["Americano"]["reasons"]))

    def test_repeated_ingredient_requirements_are_aggregated(self):
        data = self.copy_data()
        duplicate = app.EX.ExtraCoffeeRequirement
        data.add((app.EX.AmericanoRecipe, app.EX.hasRequirement, duplicate))
        data.add((duplicate, RDF.type, app.EX.RecipeRequirement))
        data.add((duplicate, app.EX.ingredient, app.EX.Coffee))
        data.add((duplicate, app.EX.requiredGrams, Literal(Decimal(18), datatype=XSD.decimal)))
        rows = app.recommend(app.prepare(data))
        americano = next(row for row in rows if row["menu_id"] == str(app.EX.Americano))
        coffee = next(row for row in americano["ingredients"] if row["ingredient_id"] == str(app.EX.Coffee))
        self.assertEqual(Decimal(coffee["needed_g"]), Decimal(36))

    def test_missing_profile_is_rejected(self):
        data = self.copy_data()
        data.remove((app.EX.OatMilk, app.EX.profileComplete, None))
        with self.assertRaisesRegex(app.DomainError, "SHACL"):
            app.prepare(data)

    def test_negative_and_duplicate_stock_are_rejected(self):
        negative = self.copy_data()
        negative.set((app.EX.StockCoffee, app.EX.availableGrams, Literal(Decimal(-1), datatype=XSD.decimal)))
        with self.assertRaisesRegex(app.DomainError, "SHACL"):
            app.prepare(negative)
        duplicate = self.copy_data()
        for predicate, value in list(duplicate.predicate_objects(app.EX.StockCoffee)):
            duplicate.add((app.EX.DuplicateStock, predicate, value))
        with self.assertRaisesRegex(app.DomainError, "재고 레코드는 하나"):
            app.prepare(duplicate)

    def test_invalid_requests_are_rejected(self):
        for kwargs in ({"quantity": 0}, {"budget": -1}, {"customer": app.EX.Unknown}, {"store": app.EX.Unknown}):
            with self.subTest(kwargs=kwargs), self.assertRaises(app.DomainError):
                app.recommend(self.graph, **kwargs)
        with self.assertRaises(app.DomainError):
            app.entity_id("Minsu . ?s ?p ?o")

    def test_order_persists_stock_and_rechecks_after_reload(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / "state.ttl"
            result = app.place_order(state, app.EX.OatLatte)
            persisted = app.load_data(state)
            self.assertEqual(persisted.value(app.EX.StockCoffee, app.EX.availableGrams).toPython(), Decimal(62))
            self.assertEqual(persisted.value(app.EX.StockOat, app.EX.availableGrams).toPython(), Decimal(100))
            self.assertEqual(len(list(persisted.subjects(RDF.type, app.EX.Order))), 1)
            self.assertEqual(result["total_price"], 4500)
            self.assertFalse(list(persisted.triples((None, app.EX.containsIngredient, None))))
            graph = app.prepare(persisted)
            self.assertIn((app.EX.Minsu, app.EX.placedOrder, next(persisted.subjects(RDF.type, app.EX.Order))), graph)
            before = state.read_bytes()
            with self.assertRaisesRegex(app.DomainError, "STOCK"):
                app.place_order(state, app.EX.OatLatte)
            self.assertEqual(state.read_bytes(), before)
            self.assertFalse(state.with_suffix(".ttl.lock").exists())

    def test_rejected_order_does_not_create_state(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / "state.ttl"
            with self.assertRaisesRegex(app.DomainError, "ALLERGEN"):
                app.place_order(state, app.EX.MilkLatte)
            self.assertFalse(state.exists())
            self.assertFalse(state.with_suffix(".ttl.lock").exists())

    def test_existing_lock_blocks_order_without_changing_state(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / "state.ttl"
            lock = state.with_suffix(".ttl.lock")
            lock.write_text("other process", encoding="utf-8")
            with self.assertRaisesRegex(app.DomainError, "처리 중"):
                app.place_order(state, app.EX.Americano)
            self.assertTrue(lock.exists())
            self.assertFalse(state.exists())


if __name__ == "__main__":
    unittest.main()
