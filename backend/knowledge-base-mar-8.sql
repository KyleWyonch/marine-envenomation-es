CREATE TABLE IF NOT EXISTS Taxonomy (
    taxon_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    rank TEXT NOT NULL CHECK (rank IN ('species', 'genus', 'family', 'order', 'class', 'phylum', 'kingdom', 'domain')),
    parent_id INTEGER,
    FOREIGN KEY (parent_id) REFERENCES Taxonomy(taxon_id)
);

-- Index for fast hierarchical lookups
CREATE INDEX IF NOT EXISTS idx_taxonomy_hierarchy ON Taxonomy(parent_id, name);

CREATE TABLE IF NOT EXISTS Species (
    species_id INTEGER PRIMARY KEY AUTOINCREMENT,
    taxon_id INTEGER NOT NULL,
    venomous INTEGER DEFAULT 0,  -- 0 = FALSE, 1 = TRUE
    description TEXT,
    FOREIGN KEY (taxon_id) REFERENCES Taxonomy(taxon_id)
);

-- Index for species lookups
CREATE INDEX IF NOT EXISTS idx_species_taxon ON Species(taxon_id);

CREATE TABLE IF NOT EXISTS Common_Names (
    common_name_id INTEGER PRIMARY KEY AUTOINCREMENT,
    species_id INTEGER NOT NULL,
    common_name TEXT NOT NULL,
    language TEXT DEFAULT 'English',
    FOREIGN KEY (species_id) REFERENCES Species(species_id)
);

-- Index for common name searches
CREATE INDEX IF NOT EXISTS idx_common_names ON Common_Names(species_id, common_name);

CREATE TABLE IF NOT EXISTS Venom_Properties (
    venom_id INTEGER PRIMARY KEY AUTOINCREMENT,
    species_id INTEGER NOT NULL,
    toxins TEXT NOT NULL,
    venom_type TEXT NOT NULL CHECK (venom_type IN ('neurotoxic', 'cytotoxic', 'hemotoxic', 'myotoxic', 'cardiotoxic')),
    delivery_mechanism TEXT NOT NULL,
    LD50 REAL DEFAULT NULL,
    molecular_weight REAL DEFAULT NULL,
    uncertainty REAL DEFAULT 1.0,
    FOREIGN KEY (species_id) REFERENCES Species(species_id)
);

-- Index for venom type searches
CREATE INDEX IF NOT EXISTS idx_venom_properties ON Venom_Properties(species_id, venom_type);

CREATE TABLE IF NOT EXISTS Envenomation_Symptoms (
    symptom_id INTEGER PRIMARY KEY AUTOINCREMENT,
    species_id INTEGER NOT NULL,
    symptom TEXT NOT NULL,
    onset_time TEXT DEFAULT 'Immediate',
    duration TEXT DEFAULT NULL,
    uncertainty REAL DEFAULT 1.0,
    FOREIGN KEY (species_id) REFERENCES Species(species_id)
);

-- Index for symptom searches
CREATE INDEX IF NOT EXISTS idx_symptoms ON Envenomation_Symptoms(species_id, symptom);

CREATE TABLE IF NOT EXISTS Treatment_Protocols (
    treatment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    species_id INTEGER NOT NULL,
    first_aid TEXT,
    hospital_treatment TEXT,
    prognosis TEXT,
    uncertainty REAL DEFAULT 1.0,
    FOREIGN KEY (species_id) REFERENCES Species(species_id)
);

-- Index for treatment lookups
CREATE INDEX IF NOT EXISTS idx_treatment_protocols ON Treatment_Protocols(species_id);

CREATE TABLE IF NOT EXISTS Antivenom (
    antivenom_id INTEGER PRIMARY KEY AUTOINCREMENT,
    species_id INTEGER NOT NULL,
    antivenom_name TEXT NOT NULL,
    availability TEXT DEFAULT 'none',
    effectiveness REAL DEFAULT NULL,
    FOREIGN KEY (species_id) REFERENCES Species(species_id)
);

-- Index for antivenom lookups
CREATE INDEX IF NOT EXISTS idx_antivenom ON Antivenom(species_id);

CREATE TABLE IF NOT EXISTS References (
    reference_id INTEGER PRIMARY KEY AUTOINCREMENT,
    species_id INTEGER NOT NULL,
    citation TEXT NOT NULL,
    url TEXT DEFAULT NULL,
    FOREIGN KEY (species_id) REFERENCES Species(species_id)
);

-- Index for reference lookups
CREATE INDEX IF NOT EXISTS idx_references ON References(species_id);

CREATE TABLE IF NOT EXISTS Habitat (
    habitat_id INTEGER PRIMARY KEY AUTOINCREMENT,
    species_id INTEGER NOT NULL,
    geographic_range TEXT,
    depth_range TEXT DEFAULT NULL,
    FOREIGN KEY (species_id) REFERENCES Species(species_id)
);

-- Index for habitat lookups
CREATE INDEX IF NOT EXISTS idx_habitat ON Habitat(species_id);

CREATE TABLE IF NOT EXISTS Medical_Severity (
    severity_id INTEGER PRIMARY KEY AUTOINCREMENT,
    species_id INTEGER NOT NULL,
    severity_rating TEXT NOT NULL CHECK (severity_rating IN ('mild', 'moderate', 'severe', 'lethal')),
    lethality INTEGER DEFAULT 0,  -- 0 = FALSE, 1 = TRUE
    FOREIGN KEY (species_id) REFERENCES Species(species_id)
);

-- Index for severity lookups
CREATE INDEX IF NOT EXISTS idx_medical_severity ON Medical_Severity(species_id);

WITH RECURSIVE TaxonHierarchy AS (
    SELECT taxon_id, name, rank, parent_id
    FROM Taxonomy
    WHERE name = 'Scorpaenidae'
    UNION ALL
    SELECT t.taxon_id, t.name, t.rank, t.parent_id
    FROM Taxonomy t
    INNER JOIN TaxonHierarchy th ON t.parent_id = th.taxon_id
)
SELECT * FROM TaxonHierarchy;

CREATE VIEW IF NOT EXISTS Species_Venom_Info AS
SELECT s.species_id, t.name AS scientific_name, vp.toxins, vp.venom_type, vp.delivery_mechanism
FROM Species s
INNER JOIN Taxonomy t ON s.taxon_id = t.taxon_id
INNER JOIN Venom_Properties vp ON s.species_id = vp.species_id;

CREATE VIEW IF NOT EXISTS Species_Symptoms_Treatment AS
SELECT s.species_id, t.name AS scientific_name, es.symptom, tp.first_aid, tp.hospital_treatment
FROM Species s
INNER JOIN Taxonomy t ON s.taxon_id = t.taxon_id
LEFT JOIN Envenomation_Symptoms es ON s.species_id = es.species_id
LEFT JOIN Treatment_Protocols tp ON s.species_id = tp.species_id;
