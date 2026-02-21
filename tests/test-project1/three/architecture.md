# Architecture

Overview of the internal design of Test Project 1.

## Components

- **Core** — business logic and data processing
- **API** — HTTP interface layer
- **CLI** — command-line interface

## Data Flow

```
CLI → Core → Storage
API → Core → Storage
```
