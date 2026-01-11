# Principles of Database Systems(H) - Review

[TOC]

## Overview

### Normal Form

1NF: **Simple attributes.**

2NF: **Attributes depend on the full key.**

3NF: **Non-key attributes do not depend on each other.**

### Entity: Has a life cycle.

### Relation: Connect to entities, no independent life.

### E/R Diagram

### Cardinality: (1, n), (0, n), (m, n)

## Grammar

### Types

#### Text

- `char(n)`, `varchar(n)`
- `clob`, `text`

#### Number

- `numeric(p, s)`, `decimal(p, s)`
- `int`, `float`

#### Date

- `date`, `timestamp`, `datetime`, e.t.c.

#### Binary

- `row`, `varbinary`
- `blob`
- `bytea`(PostgreSQL)

### Foreign Key

`CONSTRAINT cstr_name FOREIGN KEY(key_name) REFERENCES table_name(foreign_key_name)`

![image-20260106181607257](./assets/image-20260106181607257.png)

### Tips

`AND` has higher priority than `OR`.

`<>` equals to `!=`.

`NULL` is not comparable. Use `IS NULL` or `IS NOT NULL`.

**Concatenation:** 

- `||` (Mostly)
- `+` (SQL Server)
- `CONCAT(a, b)` (MySQL)

### Functions



### Examples

#### Create

```sql
CREATE TABLE currencies (
    currency_code CHAR(3) NOT NULL,
    currency_name TEXT NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_currencies PRIMARY KEY (currency_code),
    CONSTRAINT uq_currencies_name UNIQUE (currency_name),
    CONSTRAINT ck_currencies_code_upper CHECK (currency_code = UPPER(currency_code)::CHAR(3))
);

CREATE TABLE countries (
    country_code  CHAR(2) NOT NULL,
    country_name  TEXT NOT NULL,
    continent     TEXT NOT NULL,
    currency_code CHAR(3) NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_countries PRIMARY KEY (country_code),
    CONSTRAINT uq_countries_name UNIQUE (country_name),
    CONSTRAINT fk_countries_currency FOREIGN KEY (currency_code) REFERENCES currencies(currency_code),
    CONSTRAINT ck_countries_code_upper CHECK (country_code = UPPER(country_code)::CHAR(2))
);

CREATE TABLE people (
    person_id  INTEGER GENERATED ALWAYS AS IDENTITY,
    first_name TEXT,
    surname    TEXT NOT NULL,
    born_year  SMALLINT NOT NULL,
    died_year  SMALLINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_people PRIMARY KEY (person_id),
    CONSTRAINT uq_people_natural UNIQUE (first_name, surname, born_year),
    CONSTRAINT ck_people_years CHECK (
        born_year BETWEEN 1800 AND 2100 AND
        (died_year IS NULL OR (died_year BETWEEN 1800 AND 2100 AND died_year >= born_year))
    )
);

CREATE TABLE movies (
    movie_id        INTEGER GENERATED ALWAYS AS IDENTITY,
    title           TEXT NOT NULL,
    production_year SMALLINT NOT NULL,
    country_code    CHAR(2) NOT NULL,
    color           CHAR(1) NOT NULL DEFAULT 'Y',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_movies PRIMARY KEY (movie_id),
    CONSTRAINT uq_movies_natural UNIQUE (title, country_code, production_year),
    CONSTRAINT fk_movies_country FOREIGN KEY (country_code) REFERENCES countries(country_code),
    CONSTRAINT ck_movies_year CHECK (production_year BETWEEN 1888 AND 2100),
    CONSTRAINT ck_movies_color CHECK (color IN ('Y','N'))
);

CREATE TABLE movie_releases (
    movie_id        INTEGER NOT NULL,
    country_code    CHAR(2) NOT NULL,
    release_date    DATE NOT NULL,
    runtime_minutes SMALLINT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_movie_releases PRIMARY KEY (movie_id, country_code),
    CONSTRAINT fk_movie_releases_movie FOREIGN KEY (movie_id) REFERENCES movies(movie_id),
    CONSTRAINT fk_movie_releases_country FOREIGN KEY (country_code) REFERENCES countries(country_code),
    CONSTRAINT ck_movie_releases_runtime CHECK (runtime_minutes IS NULL OR runtime_minutes > 0)
);

CREATE TABLE credits (
    movie_id       INTEGER NOT NULL,
    person_id      INTEGER NOT NULL,
    role           CHAR(1) NOT NULL DEFAULT 'A',
    character_name TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_credits PRIMARY KEY (movie_id, person_id, role),
    CONSTRAINT fk_credits_movie FOREIGN KEY (movie_id) REFERENCES movies(movie_id),
    CONSTRAINT fk_credits_person FOREIGN KEY (person_id) REFERENCES people(person_id),
    CONSTRAINT ck_credits_role CHECK (role IN ('A','D'))
);

```

