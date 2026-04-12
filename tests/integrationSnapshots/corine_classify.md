<!-- man_hours: 0.0 -->
# CORINE Land Cover - classify()

**Generated:** 2026-04-03 10:26 UTC
**Run ID:** 20260403T102652_8572b44b
**Description:** Fetch CLC features + ring classification
**Sites:** 3 processed, 0 successful, 0 failed

---

## RO - Rovinari

- **Coordinates:** 44.1456, 23.1234
- **Status:** PASS (2631 ms)
- **Summary:** 14 features, 3 rings, dev=1256.5ha

<details>
<summary>Full response</summary>

```json
{
  "lat": 44.1456,
  "lon": 23.1234,
  "rings": [
    {
      "label": "0-500m",
      "inner_m": 0,
      "outer_m": 500,
      "total_area_ha": 78.53,
      "by_class": {
        "211": 78.532
      },
      "developable_ha": 78.532
    },
    {
      "label": "500m-1km",
      "inner_m": 500,
      "outer_m": 1000,
      "total_area_ha": 235.6,
      "by_class": {
        "211": 235.596
      },
      "developable_ha": 235.596
    },
    {
      "label": "1-2km",
      "inner_m": 1000,
      "outer_m": 2000,
      "total_area_ha": 942.38,
      "by_class": {
        "211": 942.383
      },
      "developable_ha": 942.383
    }
  ],
  "total_developable_ha": 1256.511,
  "source": "corine_wfs",
  "error": null
}
```

</details>

---

## PL - Bełchatów

- **Coordinates:** 51.2644, 19.3278
- **Status:** PASS (651 ms)
- **Summary:** 64 features, 3 rings, dev=677.2ha

<details>
<summary>Full response</summary>

```json
{
  "lat": 51.2644,
  "lon": 19.3278,
  "rings": [
    {
      "label": "0-500m",
      "inner_m": 0,
      "outer_m": 500,
      "total_area_ha": 78.53,
      "by_class": {
        "121": 78.532
      },
      "developable_ha": 78.532
    },
    {
      "label": "500m-1km",
      "inner_m": 500,
      "outer_m": 1000,
      "total_area_ha": 235.6,
      "by_class": {
        "121": 191.599,
        "312": 40.3,
        "324": 3.697
      },
      "developable_ha": 191.599
    },
    {
      "label": "1-2km",
      "inner_m": 1000,
      "outer_m": 2000,
      "total_area_ha": 942.38,
      "by_class": {
        "121": 303.663,
        "131": 96.537,
        "231": 0.199,
        "242": 6.688,
        "312": 393.739,
        "324": 141.558
      },
      "developable_ha": 407.087
    }
  ],
  "total_developable_ha": 677.217,
  "source": "corine_wfs",
  "error": null
}
```

</details>

---

## CZ - Tušimice

- **Coordinates:** 50.3928, 13.3278
- **Status:** PASS (1590 ms)
- **Summary:** 73 features, 3 rings, dev=907.1ha

<details>
<summary>Full response</summary>

```json
{
  "lat": 50.3928,
  "lon": 13.3278,
  "rings": [
    {
      "label": "0-500m",
      "inner_m": 0,
      "outer_m": 500,
      "total_area_ha": 78.53,
      "by_class": {
        "121": 6.96,
        "211": 15.309,
        "231": 0.558,
        "313": 55.706
      },
      "developable_ha": 22.826
    },
    {
      "label": "500m-1km",
      "inner_m": 500,
      "outer_m": 1000,
      "total_area_ha": 235.6,
      "by_class": {
        "121": 63.907,
        "211": 45.422,
        "231": 37.609,
        "313": 88.657
      },
      "developable_ha": 146.938
    },
    {
      "label": "1-2km",
      "inner_m": 1000,
      "outer_m": 2000,
      "total_area_ha": 942.38,
      "by_class": {
        "121": 177.541,
        "131": 0.567,
        "211": 216.725,
        "222": 30.803,
        "231": 342.489,
        "311": 2.444,
        "313": 141.734,
        "324": 30.08
      },
      "developable_ha": 737.322
    }
  ],
  "total_developable_ha": 907.086,
  "source": "corine_wfs",
  "error": null
}
```

</details>

---

