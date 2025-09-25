# ODIN-AI Search API Documentation

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication
Currently no authentication required (development mode)

---

## 🔍 Search Endpoints

### 1. Main Search
**GET** `/search`

Performs a comprehensive search across bids, documents, and companies.

#### Query Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| query | string | Yes | - | Search query text |
| type | string | No | "all" | Search type: all, bid, document, company |
| sort | string | No | "relevance" | Sort order: relevance, date_desc, date_asc, price_desc, price_asc |
| page | integer | No | 1 | Page number (1-based) |
| size | integer | No | 20 | Results per page (max: 100) |
| filters | object | No | {} | JSON filter object |

#### Filter Object Structure
```json
{
  "startDate": "2025-09-01",
  "endDate": "2025-09-30",
  "minPrice": 10000000,
  "maxPrice": 100000000,
  "organization": "서울시",
  "industry": "IT",
  "status": "active",
  "region": "서울",
  "tags": ["긴급", "중요"],
  "excludeClosed": true,
  "onlyUrgent": false,
  "hasAttachments": true
}
```

#### Response
```json
{
  "query": "소프트웨어",
  "searchType": "all",
  "results": [
    {
      "type": "bid",
      "id": "12345",
      "bidNoticeNo": "2025-B-001",
      "title": "소프트웨어 개발 용역",
      "organization": "서울시",
      "price": 50000000,
      "deadline": "2025-10-15",
      "status": "active",
      "score": 95.5,
      "highlight": "<mark>소프트웨어</mark> 개발 용역"
    }
  ],
  "totalCount": 150,
  "pageInfo": {
    "currentPage": 1,
    "pageSize": 20,
    "totalPages": 8,
    "totalItems": 150,
    "hasNext": true,
    "hasPrev": false
  },
  "facets": {
    "organizations": [
      {"name": "서울시", "count": 45},
      {"name": "경기도", "count": 32}
    ],
    "status": [
      {"name": "active", "count": 120},
      {"name": "closed", "count": 30}
    ]
  }
}
```

### 2. Search Suggestions
**GET** `/search/suggestions`

Returns autocomplete suggestions based on partial query.

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| query | string | Yes | Partial search query (min 2 chars) |
| limit | integer | No | Max suggestions (default: 10) |

#### Response
```json
{
  "query": "소프",
  "suggestions": [
    "소프트웨어",
    "소프트웨어 개발",
    "소프트웨어 유지보수"
  ],
  "count": 3
}
```

### 3. Search Facets
**GET** `/search/facets`

Returns available filter options and counts.

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| type | string | No | Search type filter |
| filters | object | No | Current filters |

#### Response
```json
{
  "organizations": [
    {"name": "서울시", "count": 234},
    {"name": "경기도", "count": 189}
  ],
  "status": [
    {"name": "active", "count": 450},
    {"name": "pending", "count": 123}
  ],
  "priceRanges": [
    {"range": "0-10M", "count": 234},
    {"range": "10M-50M", "count": 156}
  ]
}
```

### 4. Recent Searches
**GET** `/search/recent`

Returns user's recent search queries.

#### Response
```json
{
  "searches": [
    {
      "query": "소프트웨어",
      "timestamp": "2025-09-23T10:30:00Z",
      "resultCount": 45
    }
  ]
}
```

---

## 📊 Bid-Specific Endpoints

### 5. Search Bids
**GET** `/search/bids`

Search specifically within bid announcements.

#### Query Parameters
Same as main search endpoint

#### Additional Bid Filters
```json
{
  "bidMethod": "electronic",
  "contractType": "service",
  "urgency": "high",
  "subcontractAllowed": true,
  "regionRestriction": "서울"
}
```

### 6. Get Bid Details
**GET** `/bids/{bid_id}`

Returns detailed information about a specific bid.

#### Response
```json
{
  "id": "12345",
  "bidNoticeNo": "2025-B-001",
  "title": "소프트웨어 개발 용역",
  "organization": "서울시",
  "announcementDate": "2025-09-15",
  "deadline": "2025-10-15",
  "expectedPrice": 50000000,
  "bidMethod": "electronic",
  "status": "active",
  "extractedInfo": {
    "duration": "6개월",
    "qualifications": ["정보통신공사업", "소프트웨어사업자"],
    "specialConditions": ["지역제한: 서울"],
    "subcontractRatio": 30
  },
  "attachments": [
    {
      "filename": "과업지시서.hwp",
      "size": 2048000,
      "url": "/api/v1/files/download/xyz"
    }
  ],
  "schedule": [
    {
      "event": "입찰마감",
      "date": "2025-10-15 14:00"
    }
  ]
}
```

---

## 📄 Document Endpoints

### 7. Search Documents
**GET** `/search/documents`

Search within uploaded documents.

#### Query Parameters
Same as main search, plus:
| Parameter | Type | Description |
|-----------|------|-------------|
| fileType | string | Filter by file type (hwp, pdf, docx) |
| minSize | integer | Minimum file size in bytes |
| maxSize | integer | Maximum file size in bytes |

### 8. Get Document
**GET** `/documents/{document_id}`

Returns document metadata and extracted content.

### 9. Download Document
**GET** `/documents/{document_id}/download`

Downloads the original document file.

---

## 🏢 Company Endpoints

### 10. Search Companies
**GET** `/search/companies`

Search company information.

#### Query Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| businessNumber | string | Business registration number |
| industry | string | Industry classification |
| region | string | Company location |

---

## 🔧 Utility Endpoints

### 11. Health Check
**GET** `/health`

Returns API health status.

#### Response
```json
{
  "status": "healthy",
  "timestamp": "2025-09-23T10:00:00Z",
  "version": "1.0.0",
  "services": {
    "database": "connected",
    "redis": "connected",
    "search": "ready"
  }
}
```

### 12. Search Health
**GET** `/search/health`

Returns search service specific health metrics.

#### Response
```json
{
  "status": "operational",
  "indexCount": 15000,
  "lastIndexUpdate": "2025-09-23T09:00:00Z",
  "cacheHitRate": 0.85,
  "avgResponseTime": 45
}
```

---

## 📈 Performance Endpoints

### 13. Search Metrics
**GET** `/search/metrics`

Returns search performance metrics.

#### Response
```json
{
  "totalSearches": 10000,
  "avgResponseTime": 45,
  "cacheHitRate": 0.85,
  "topQueries": [
    {"query": "소프트웨어", "count": 234},
    {"query": "건설", "count": 189}
  ],
  "errorRate": 0.002
}
```

---

## 🔄 WebSocket Endpoints

### 14. Real-time Search Updates
**WS** `/ws/search`

WebSocket connection for real-time search updates.

#### Message Format
```json
{
  "type": "search",
  "query": "소프트웨어"
}
```

#### Response Stream
```json
{
  "type": "result",
  "data": {...},
  "timestamp": "2025-09-23T10:00:00Z"
}
```

---

## ⚠️ Error Responses

All endpoints return standard error responses:

### 400 Bad Request
```json
{
  "error": "Bad Request",
  "message": "Invalid query parameter",
  "details": {
    "field": "page",
    "value": 0,
    "constraint": "Must be >= 1"
  }
}
```

### 404 Not Found
```json
{
  "error": "Not Found",
  "message": "Resource not found",
  "resource": "bid",
  "id": "12345"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred",
  "requestId": "req_xyz123",
  "timestamp": "2025-09-23T10:00:00Z"
}
```

---

## 🔐 Rate Limiting

| Endpoint Type | Rate Limit | Window |
|--------------|------------|---------|
| Search | 100 requests | 1 minute |
| Suggestions | 200 requests | 1 minute |
| Download | 50 requests | 1 minute |
| WebSocket | 10 connections | Per IP |

---

## 📝 Examples

### Basic Search
```bash
curl "http://localhost:8000/api/v1/search?query=소프트웨어"
```

### Filtered Search
```bash
curl "http://localhost:8000/api/v1/search?query=건설&type=bid&sort=date_desc&page=1&size=10"
```

### Complex Filter
```bash
curl -X GET "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SI사업",
    "filters": {
      "minPrice": 10000000,
      "maxPrice": 100000000,
      "status": "active"
    }
  }'
```

### WebSocket Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/search');

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'search',
    query: '소프트웨어'
  }));
};

ws.onmessage = (event) => {
  const result = JSON.parse(event.data);
  console.log('Search result:', result);
};
```

---

## 🚀 Best Practices

1. **Use Caching Headers**: Respect Cache-Control headers for better performance
2. **Pagination**: Always use pagination for large result sets
3. **Filter Early**: Apply filters to reduce server load
4. **Batch Requests**: Use bulk endpoints when available
5. **Handle Errors**: Implement proper error handling and retries
6. **Monitor Rate Limits**: Track X-RateLimit headers

---

## 📊 Response Headers

| Header | Description |
|--------|-------------|
| X-Total-Count | Total number of results |
| X-Page-Count | Total number of pages |
| X-RateLimit-Limit | Rate limit ceiling |
| X-RateLimit-Remaining | Remaining requests |
| X-RateLimit-Reset | Reset timestamp |
| X-Response-Time | Server processing time |
| Cache-Control | Caching directives |

---

## 🔄 Changelog

### Version 1.0.0 (2025-09-23)
- Initial API release
- Full-text search implementation
- Redis caching integration
- WebSocket support
- Comprehensive filtering