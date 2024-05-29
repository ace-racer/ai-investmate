from spacy_llm.util import assemble
from tqdm import tqdm
from pathlib import Path
import os


# Define a set of valid relations and their corresponding entity pairs
valid_relations = {
    "LocatedIn": [("COMPANY", "COUNTRY"), ("COUNTRY", "COMPANY"), ("FUND", "COUNTRY"), ( "COUNTRY", "FUND"), ("STOCK", "COUNTRY"), ("COUNTRY", "STOCK")],
    "BelongsTo": [("COMPANY", "SECTOR"), ("SECTOR", "COMPANY"), ("SECTOR", "FUND"), ("FUND", "SECTOR")],
    "InvestsIn": [
        ("INVESTOR", "COMPANY"), ("COMPANY", "INVESTOR"),
        ("INVESTOR", "FUND"), ("FUND", "INVESTOR"),
        ("FUND", "STOCK"), ("STOCK", "FUND")
    ],
    "ManagedBy": [("FUND", "EXECUTIVE"), ("EXECUTIVE", "FUND")],
    "PartOf": [("COMPANY", "FUND"), ("FUND", "COMPANY"), ("FUND", "FUND")],
    "HasSector": [("COUNTRY", "SECTOR"), ("SECTOR", "COUNTRY"), ("FUND", "SECTOR"), ("SECTOR", "FUND")],
    "EmployedBy": [("EXECUTIVE", "COMPANY"), ("COMPANY", "EXECUTIVE")],
    "ListedIn": [("STOCK", "STOCK_EXCHANGE"), ("STOCK_EXCHANGE", "STOCK")],
}


def check_relation(source_entity, relation, target_entity):
    print("Checking relation")
    print(f"{source_entity.text}({source_entity.label_}) -> {target_entity.text}({target_entity.label_})[{relation}]")
    entity_pair = (source_entity.label_, target_entity.label_)
    reversed_entity_pair = (target_entity.label_, source_entity.label_)

    if relation in valid_relations:
        if entity_pair in valid_relations[relation] or reversed_entity_pair in valid_relations[relation]:
            return True
    
    print(f"Could not map: {source_entity.text}({source_entity.label_}) -> {target_entity.text}({target_entity.label_})[{relation}]")
    return False

def extract_entities_and_relations(texts: list[str]) -> tuple[set[str], list[tuple[str, str, str]], dict[str, str]]:
    ner_nlp = assemble(os.path.join(Path(__file__).parent, "ner_config.cfg"), overrides={"components.ner.task.examples.path": os.path.join(Path(__file__).parent, "ner_examples.yml")})
    rel_nlp = assemble(os.path.join(Path(__file__).parent, "rel_config.cfg"))
    entities = set()
    relations = []
    all_entity_labels = {}

    for text in tqdm(texts):
        print(f"Extracting entities from {text}")
        doc = ner_nlp(text)
        # print([(ent.text, ent.label_) for ent in doc.ents])
        for ent in doc.ents:
            entities.add(ent.text)
            all_entity_labels[ent.text] = ent.label_

        entity_labels = set(ent.label_ for ent in doc.ents)
        print(f"Distinct entity labels: {entity_labels}")
        if len(entity_labels) >= 2:
            print(f"Extracting relations...{doc}")
            rel_doc = rel_nlp(doc)
            for r in rel_doc._.rel:
                print(f"Relation: {doc.ents[r.dep]} [{r.relation}] {doc.ents[r.dest]}")
                if check_relation(doc.ents[r.dep], r.relation, doc.ents[r.dest]):
                    relations.append((str(doc.ents[r.dep]), r.relation, str(doc.ents[r.dest])))
                else:
                    print("Current detected relation is invalid")
        else:
            print("Less than 2 unique entities in current doc")


    return entities, relations, all_entity_labels