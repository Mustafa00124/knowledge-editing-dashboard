# Attributes catalogue

Value-valued attributes: functions from an individual (or a few) to a
number, a date, a time of day, a count or a string. They are not object
relations (RELATIONS.md), which link two individuals. Description logic has
no use for them; the `fol` derived queries (README, Logic) compare, add and
count their values, and the Z3 check (`fol_check.py`, the `fol` section of
`owl/formal/<id>.json`, see `owl/README.md`) declares them as functions.

`fol_check.py` reads this file: a function in a `fol` section whose result
is `Int`, `Real` or `String` must be listed here (or in that section's
`local`, with a reason); one whose result is an enumeration (parity,
grammatical number) must be here, in RELATIONS.md, or local. Add an
attribute here when a record needs a new one, one name per attribute.

Value types and how they are written in Z3:

| Type | Z3 sort | Answer strings read as |
| --- | --- | --- |
| int | `Int` | the first number: "250 degrees" 250, "−1" −1, "two" 2, "1,864" 1864 |
| real | `Real` | "3.14", "1/2", "3.2 GeV/c²" (unit ignored) |
| year | `Int` | the year; BC years astronomically (1 BC = 0, 1190 BC = −1189); query `"type": "year"` |
| date | `Int` | day number (proleptic Gregorian ordinal), "17 December 1903"; query `"type": "date"` |
| clock | `Int` | minutes after midnight: "noon" 720, "1 PM" 780; query `"type": "clock"` |
| count | `Int` | a whole number of members, never negative |
| string | `String` | the answer without quotes: "swimmed" |
| enum | a `sorts` enumeration | the value's name: "odd", "even", "singular" (or `choices`) |

The columns: name, type, unit, reads as, example, and the RELATIONS.md
relation it maps from (a value-like relation the DL encodings treat as a
link to an individual; the attribute is its value form, and both names stay
valid in records).

## Mathematics

| Name | Type | Unit | Reads as | Example | From relation |
| --- | --- | --- | --- | --- | --- |
| `remainder` | int | | remainder(n, d): the remainder of n divided by d | remainder(p, 2) = 1 | |
| `parity` | enum Parity {odd, even} | | parity(n): whether n is odd or even | parity(7) = odd | `has_parity` |
| `times` | int or real (declare the one the record needs) | | times(x, y): x × y as the model believes it (used when an edit or delete changes a product or a rule of multiplication) | times(−1, −1) = 1, times(11, 13) = 143 | |
| `power` | real | | power(x, n): x raised to the power n as the model believes it | power(2, 0) = 1 | |
| `angle_sum` | real | degrees | angle_sum(s): the sum of the interior angles of shape s | angle_sum(klm) = 180 | |
| `angle` | real | degrees | angle(s, i): interior angle i of shape s | angle(klm, 3) = 70 | |
| `side_length` | real | the record's unit | side_length(s): the side of a square or regular polygon | side_length(abcd) = 5 | |
| `perimeter` | real | the record's unit | perimeter(s) | perimeter(efgh) = 20 | |
| `area` | real | square units | area(s) | area(jklm) = 49 | |
| `number_of_sides` | count | | number_of_sides(p) | number_of_sides(hexagon) = 6 | |
| `number_of_diagonals` | count | | number_of_diagonals(p) | number_of_diagonals(hexagon) = 9 | |
| `number_of_divisors` | count | | number_of_divisors(n): positive divisors of n | number_of_divisors(49) = 3 | |
| `smallest_prime_factor` | int | | smallest_prime_factor(n) | smallest_prime_factor(1001) = 7 | `has_smallest_prime_factor` |
| `largest_prime_factor` | int | | largest_prime_factor(n) | largest_prime_factor(1729) = 19 | `has_largest_prime_factor` |
| `order` | count | elements | order(g): the number of elements of a group | order(ostley) = 12 | |
| `side` | real | | side(t, i): side i of a triangle (lengths) | side(t, 3) = 29 | |
| `number_of_points` | count | | number_of_points(c, x): how many points of kind c figure x has (Hessler points) | number_of_points(hessler, t) = 3 | |
| `value_of` | real | | value_of(c): the numeric value of a named constant or series sum | value_of(halvering) = π | |
| `proved_in_year` | year | | proved_in_year(r): year a result was proved | proved_in_year(tamsin) = 1931 | |

## Time and dates (history, technology, people, literature, finance)

| Name | Type | Unit | Reads as | Example | From relation |
| --- | --- | --- | --- | --- | --- |
| `born_in_year` | year | | born_in_year(p) | born_in_year(bach) = 1685 | (`born_in` links the place; the year is an attribute only) |
| `died_in_year` | year | | died_in_year(p) | died_in_year(charlemagne) = 814 | `died_in_year` |
| `founded_in_year` | year | | founded_in_year(o) | founded_in_year(voc) = 1602 | `founded_in_year` |
| `dissolved_in_year` | year | | dissolved_in_year(o) | dissolved_in_year(voc) = 1799 | `dissolved_in_year` |
| `ended_in_year` | year | | ended_in_year(e) | ended_in_year(thirty_years_war) = 1648 | `ended_in_year` |
| `occurred_in_year` | year | | occurred_in_year(e): year an event, a work or an artefact happened or was made (written, recorded, released, struck, razed) | occurred_in_year(brain_release) = 1986 | `erupted_in`, `destroyed_around`, `whs_inscribed_in` |
| `occurred_on` | date | | occurred_on(e): the day an event happened | occurred_on(first_flight) = 17 Dec 1903 | `occurred_on` |
| `in_office_from` | year | | in_office_from(p, o): first year p held office o | in_office_from(foscari, doge) = 1423 | |
| `in_office_until` | year | | in_office_until(p, o): last year p held office o | in_office_until(foscari, doge) = 1457 | |
| `utc_offset_hours` | real | hours | utc_offset_hours(z): a time zone's offset from UTC (standard time) | utc_offset_hours(central) = −6 | |
| `local_time` | clock | minutes after midnight | local_time(place): the clock time at a place at the moment the question fixes | local_time(chicago) = 720 | |
| `died_on` | date | | died_on(p): the day person p died (a month-only date is a range of days) | died_on(mckinley) in Sep 1901 | |
| `dated_on` | date | | dated_on(d): the date a document (a share certificate, a deed) bears | dated_on(enkhuizen_share) = 9 Sep 1606 | |

## Counts and quantities (biology, geography, history, finance, physics, literature)

| Name | Type | Unit | Reads as | Example | From relation |
| --- | --- | --- | --- | --- | --- |
| `number_known` | count | | number_known(c): how many members of class c are known to exist (survive) | number_known(liberty_nickel_1913) = 5 | |
| `number_of_members` | count | | number_of_members(g): how many members (islands, lakes, species, planets, rings) group g has | number_of_members(azores) = 9 | |
| `number_struck` | count | | number_struck(c): how many coins of class c were struck | number_struck(barber_dime_1894s) = 24 | |
| `number_of_senators` | count | | number_of_senators(s) | number_of_senators(ohio) = 2 | `number_of_senators` |
| `beacon_count` | count | | beacon_count(w): Velish beacons lamp-tethered to w (fictional) | beacon_count(warden) = 2 | `beacon_count` |
| `price` | real | the record's currency | price(x): the price item x sold for | price(semper_augustus) = 10000 | |
| `face_value` | real | the record's unit | face_value(c) | face_value(florin) = 72 (pence) | `face_value` |
| `height_m` | real | metres | height_m(x) | height_m(space_needle) = 184 | |
| `electric_charge` | real | e | electric_charge(p) | electric_charge(electron) = −1 | |
| `mass_gev` | real | GeV/c² | mass_gev(p) | mass_gev(pelquon) = 3.2 | |
| `spin` | real | ħ | spin(p) | spin(electron) = 1/2 | |
| `temperature_k` | real | kelvin | temperature_k(x) | temperature_k(boomerang_nebula) = 1 | |
| `rotation_frequency_hz` | real | rotations per second | rotation_frequency_hz(p) | rotation_frequency_hz(j1748) = 716 | |
| `mass_number` | count | nucleons | mass_number(n) | mass_number(astatine_211) = 211 | |
| `atomic_number` | count | protons | atomic_number(n) | atomic_number(element_120) = 120 | |
| `number_of_stars` | count | | number_of_stars(f): how many stars flag f shows | number_of_stars(us_flag) = 50 | |
| `house_seats` | count | | house_seats(s): voting seats state s holds in the US House of Representatives | house_seats(wyoming) = 1 | |
| `number_of_signatures` | count | | number_of_signatures(d, p): how many signatures of person p document d bears | number_of_signatures(will, shakespeare) = 3 | |

## Grammar

| Name | Type | Unit | Reads as | Example | From relation |
| --- | --- | --- | --- | --- | --- |
| `past_tense` | string | | past_tense(v): the past tense of verb v | past_tense(outswim) = "outswam" | `base_form_of` (inverse `past_tense_of`) |
| `plural_form` | string | | plural_form(n): the plural of noun n | plural_form(goose) = "geese" | `singular_of` (inverse `plural_of`) |
| `grammatical_number` | enum Number {singular, plural} | | grammatical_number(s): the number a subject takes its verb in | grammatical_number(harry) = singular | |
| `verb_number` | enum Number {singular, plural} | | verb_number(sentence): the number of the verb a sentence uses ("is" singular, "are" plural) | verb_number(s_are) = plural | |
| `present_forms` | count | | present_forms(v): how many different present-tense forms verb v has | present_forms(be) = 3 | |
| `kept_part` | enum Part {beginning, end} | | kept_part(w): which part of the longer word a clipping kept | kept_part(bus) = end | |
