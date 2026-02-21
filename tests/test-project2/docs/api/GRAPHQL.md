# GraphQL API Reference

The Acme Platform GraphQL API provides a flexible query interface for all
platform resources.

## Endpoint

`POST https://api.acme.example.com/graphql`

Include `Authorization: Bearer <token>` in the request header.

## Schema Overview

### Queries

```graphql
# Fetch a user by ID
query GetUser($id: ID!) {
  user(id: $id) {
    id
    email
    name
    createdAt
    organizations {
      id
      name
    }
  }
}

# List jobs with status filter
query ListJobs($status: JobStatus) {
  jobs(status: $status) {
    edges {
      node {
        id
        type
        status
        createdAt
        completedAt
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

### Mutations

```graphql
# Create a new organization
mutation CreateOrg($input: CreateOrgInput!) {
  createOrganization(input: $input) {
    organization {
      id
      name
      slug
    }
  }
}
```

## Subscriptions

Real-time job status updates are available via WebSocket subscriptions.

```graphql
subscription OnJobUpdate($jobId: ID!) {
  jobStatusChanged(jobId: $jobId) {
    status
    progress
    message
  }
}
```

## Introspection

GraphQL introspection is enabled on non-production environments only.
In production, use the published schema file from the CI artifacts.
