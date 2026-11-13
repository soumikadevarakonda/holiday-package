# Travel Platform Database ER Diagram

This document contains a Mermaid `erDiagram` reconstructed from the
supplied schema image. It can be rendered in GitHub, VS Code (with a
Mermaid extension), or the Mermaid Live Editor.

## Mermaid ER diagram

``` mermaid
erDiagram
    COUNTRY {
        string code PK
        string name
        string timezone
    }

    DESTINATION_CITY {
        string country_code PK, FK
        string name PK
    }

    HOTEL {
        string hotel_id PK
        string city FK
        string area
        int stars
        float rating
    }

    ROOM {
        string room_id PK
        string hotel_id FK
        int max_adults
        int max_children
        int price_per_night
    }

    ROOM_AVAILABILITY {
        string room_id PK, FK
        date date PK
        int rooms_left
    }

    ATTRACTION {
        string attraction_id PK
        string city FK
        string category
        int visit_minutes
    }

    INTERCITY_LINK {
        string country_code PK, FK
        string from_city PK, FK
        string to_city PK, FK
    }

    CITY_TRANSFER {
        string transfer_id PK, FK
        string city
    }

    INTERCITY_TRANSFER {
        string transfer_id PK, FK
        string from_city
        string to_city
        boolean door_to_door
    }

    AIRPORT_TRANSFER {
        string transfer_id PK, FK
        string airport_code FK
        string city
        string area
    }

    CITY_AIRPORT {
        string country_code PK, FK
        string city_name PK, FK
        string airport_code PK, FK
    }

    LINK_TRANSFER {
        string country_code PK, FK
        string from_city PK
        string to_city PK
        string transfer_id PK, FK
    }

    TRANSFER {
        string transfer_id PK
        string type
        int duration_minutes
        string pricing
        int max_passengers
    }

    AIRPORT {
        string code PK
        string name
        string city
        string country
        string timezone
    }

    DEPARTURE_CITY {
        string city
        string airport_code FK
    }

    FLIGHT {
        string flight_id PK
        string from_airport FK
        string to_airport FK
        datetime departure_local
        datetime arrival_local
        int duration_minutes
        int seats_left
    }

    COUNTRY ||--o{ DESTINATION_CITY : contains

    DESTINATION_CITY ||--o{ HOTEL : has
    HOTEL ||--o{ ROOM : offers
    ROOM ||--o{ ROOM_AVAILABILITY : has

    DESTINATION_CITY ||--o{ ATTRACTION : contains

    DESTINATION_CITY ||--o{ INTERCITY_LINK : origin_city
    DESTINATION_CITY ||--o{ INTERCITY_LINK : destination_city

    TRANSFER ||--o| CITY_TRANSFER : subtype
    TRANSFER ||--o| INTERCITY_TRANSFER : subtype
    TRANSFER ||--o| AIRPORT_TRANSFER : subtype

    DESTINATION_CITY ||--o{ CITY_TRANSFER : operates_in
    DESTINATION_CITY ||--o{ INTERCITY_TRANSFER : starts_in
    DESTINATION_CITY ||--o{ INTERCITY_TRANSFER : ends_in
    DESTINATION_CITY ||--o{ AIRPORT_TRANSFER : serves_city

    AIRPORT ||--o{ AIRPORT_TRANSFER : serves
    DESTINATION_CITY ||--o{ CITY_AIRPORT : maps_to
    AIRPORT ||--o{ CITY_AIRPORT : serves

    INTERCITY_LINK ||--o{ LINK_TRANSFER : offers
    TRANSFER ||--o{ LINK_TRANSFER : referenced_by

    AIRPORT ||--o{ DEPARTURE_CITY : used_by
    AIRPORT ||--o{ FLIGHT : departure_airport
    AIRPORT ||--o{ FLIGHT : arrival_airport
```

## Notes and interpretation

-   Composite primary keys are marked with `PK` on each participating
    column.
-   `PK, FK` indicates a column that participates in the primary key and
    also references another table.
-   `CITY_TRANSFER`, `INTERCITY_TRANSFER`, and `AIRPORT_TRANSFER` are
    modeled as transfer subtypes using `transfer_id`.
-   `CITY_AIRPORT` is a mapping table between destination cities and
    airports.
-   `LINK_TRANSFER` associates an intercity link with an available
    transfer.
-   Some relationships and key constraints in the source image are
    represented using the visible column labels and connector lines.
    Where the image does not make a constraint fully explicit, treat the
    Mermaid relationship as a best-effort interpretation and verify it
    against the actual SQL schema before generating migrations.

## Render the diagram

1.  Copy the Mermaid code block into [Mermaid Live
    Editor](https://mermaid.live/).
2.  Or keep this `.md` file in your GitHub repository; GitHub renders
    Mermaid diagrams in Markdown.
