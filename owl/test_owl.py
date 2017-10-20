#
# examples from the manual
#

from ordf.namespace import register_ns, Namespace
register_ns("data", Namespace("http://example.org/data#"))
register_ns("ont", Namespace("http://example.org/ontology#"))

## imports required for the example
from ordf.graph import Graph, ConjunctiveGraph
from ordf.namespace import DATA, ONT, FOAF, RDF, RDFS
from ordf.term import URIRef, Literal
from ordf.vocab.owl import Class, AnnotatibleTerms, predicate, object_predicate

class Person(AnnotatibleTerms):
    def __init__(self, *av, **kw):
        super(Person, self).__init__(*av, **kw)
        self.type = FOAF.Person
    name = predicate(FOAF.name)
    homepage = predicate(FOAF.homepage)

def test_00_person():
    ## create a person
    bob = Person(DATA.bob)
    bob.name = "Bob"
    bob.homepage = URIRef("http://example.org/")

    assert FOAF.Person in bob.type
    assert "Bob" in bob.name
    assert "http://example.org/" in bob.homepage

class Country(AnnotatibleTerms):
    def __init__(self, *av, **kw):
        super(Country, self).__init__(*av, **kw)
        self.type = ONT.Country

class City(AnnotatibleTerms):
    def __init__(self, *av, **kw):
        super(City, self).__init__(*av, **kw)
        self.type = ONT.City
    country = object_predicate(ONT.country, Country)

def test_01_obj_pred():
    data = Graph()

    scotland = Country(DATA.Scotland, graph=data)
    scotland.label = "Scotland"
    
    edinburgh = City(DATA.Edinburgh, graph=data)
    edinburgh.label = "Edinburgh"
    edinburgh.country = scotland

    assert scotland in edinburgh.country

class PlaceClass(Class):
    def __init__(self, **kw):
        super(PlaceClass, self).__init__(ONT.Place, **kw)

class CountryClass(Class):
    def __init__(self, **kw):
        super(CountryClass, self).__init__(ONT.Country, **kw)
        self.subClassOf = PlaceClass(graph=self.graph)
        self.factoryClass = Country
        self.label = "Country"

class CityClass(Class):
    def __init__(self, **kw):
        super(CityClass, self).__init__(ONT.City, **kw)
        self.subClassOf = PlaceClass(graph=self.graph)
        self.factoryClass = City
        self.label = "City"

def test_02_class():
    ontology = Graph()
    data = Graph()

    scotland = Country(DATA.scotland, graph=data)
    scotland.label = "Scotland"
    
    edinburgh = City(DATA.edinburgh, graph=data)
    edinburgh.label = "Edinburgh"
    edinburgh.country = scotland

    country = CountryClass(graph=ontology, factoryGraph=data)
    city = CityClass(graph=ontology, factoryGraph=data)

    assert country.get(DATA.scotland) == scotland
    assert city.get(DATA.edinburgh) == edinburgh

def test_03_filter():
    from telescope import v

    ontology = Graph()
    data = Graph()

    country = CountryClass(graph=ontology, factoryGraph=data)
    city = CityClass(graph=ontology, factoryGraph=data)

    scotland = Country(DATA.scotland, graph=data)
    scotland.label = "Scotland"
    russia = Country(DATA.russia, graph=data)
    russia.label = "Russia"

    results = list(country.filter((v.id, RDFS.label, Literal("Russia"))))
    assert len(results) == 1
    assert 'Russia' in results[0].label

def test_04_dl():
    ontology = Graph()
    data = Graph()

    scotland = Country(DATA.scotland, graph=data)
    scotland.label = "Scotland"
    
    edinburgh = City(DATA.edinburgh, graph=data)
    edinburgh.label = "Edinburgh"
    edinburgh.country = scotland

    place = PlaceClass(graph=ontology, factoryGraph=data)
    country = CountryClass(graph=ontology, factoryGraph=data)
    city = CityClass(graph=ontology, factoryGraph=data)

    from FuXi.Rete.RuleStore import SetupRuleStore
    from FuXi.Rete.Util import generateTokenSet

    rule_store, rule_graph, network = SetupRuleStore(makeNetwork=True)
    network.reset(data)
    network.setupDescriptionLogicProgramming(ontology)
    network.feedFactsToAdd(generateTokenSet(data))

    assert place.get(DATA.scotland) == scotland
    assert place.get(DATA.edinburgh) == edinburgh
