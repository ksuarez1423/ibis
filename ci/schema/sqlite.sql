DROP TABLE IF EXISTS functional_alltypes;

CREATE TABLE functional_alltypes (
    "index" BIGINT,
    "Unnamed: 0" BIGINT,
    id BIGINT,
    bool_col BOOLEAN,
    tinyint_col BIGINT,
    smallint_col BIGINT,
    int_col BIGINT,
    bigint_col BIGINT,
    float_col FLOAT,
    double_col REAL,
    date_string_col TEXT,
    string_col TEXT,
    timestamp_col TIMESTAMP,
    year BIGINT,
    month BIGINT,
    CHECK (bool_col IN (0, 1))
);

CREATE INDEX ix_functional_alltypes_index ON "functional_alltypes" ("index");

DROP TABLE IF EXISTS awards_players;

CREATE TABLE awards_players (
    "playerID" TEXT,
    "awardID" TEXT,
    "yearID" BIGINT,
    "lgID" TEXT,
    tie TEXT,
    notes TEXT
);

DROP TABLE IF EXISTS batting;

CREATE TABLE batting (
    "playerID" TEXT,
    "yearID" BIGINT,
    stint BIGINT,
    "teamID" TEXT,
    "lgID" TEXT,
    "G" BIGINT,
    "AB" BIGINT,
    "R" BIGINT,
    "H" BIGINT,
    "X2B" BIGINT,
    "X3B" BIGINT,
    "HR" BIGINT,
    "RBI" BIGINT,
    "SB" BIGINT,
    "CS" BIGINT,
    "BB" BIGINT,
    "SO" BIGINT,
    "IBB" BIGINT,
    "HBP" BIGINT,
    "SH" BIGINT,
    "SF" BIGINT,
    "GIDP" BIGINT
);

DROP TABLE IF EXISTS diamonds;

CREATE TABLE diamonds (
    carat FLOAT,
    cut TEXT,
    color TEXT,
    clarity TEXT,
    depth FLOAT,
    "table" FLOAT,
    price BIGINT,
    x FLOAT,
    y FLOAT,
    z FLOAT
);

DROP TABLE IF EXISTS json_t;

CREATE TABLE json_t (js JSON);

INSERT INTO json_t VALUES
    ('{"a": [1,2,3,4], "b": 1}'),
    ('{"a":null,"b":2}'),
    ('{"a":"foo", "c":null}'),
    ('null'),
    ('[42,47,55]'),
    ('[]');

DROP TABLE IF EXISTS win;
CREATE TABLE win (g TEXT, x BIGINT, y BIGINT);
INSERT INTO win VALUES
    ('a', 0, 3),
    ('a', 1, 2),
    ('a', 2, 0),
    ('a', 3, 1),
    ('a', 4, 1);
