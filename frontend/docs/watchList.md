### 🔹 API: `getUserStockWatchList`

**Description:**

- get all stock from watchList for each user

**Method:** `GET`
**Endpoint:** `/api/v1/watchlists/{userId}`

**Success Response:**

```json
{
  "data": [
    { "ticker": "TSMC", "price": 1300, "change": 10 }, //price is lattest price in db change is the latest return percent (%)
    { "ticker": "AAPL", "price": 500, "change": 20 }
  ],
  "code": 1,
  "message": "WatchList successfully retrieved"
}
```

**Failure Response:**

```json
{
  "data": [],
  "code": 0,
  "message": "WatchList fail to be added"
}
```

### 🔹 API: `addStockWatchListItem`

**Description:**

- add new type of stock in watchList for user

**Method:** `POST`
**Endpoint:** `/api/v1/watchlists/{userId}`
**Content-Type:** `application/json`
**Request Body**

```json
{ "ticker": "2330.TW" }
```

**Sucess Response:**

```json
{
  "data": {
    "ticker": "2330.TW",
    "price": 1300,
    "change": 10 //price is lattest price in db change is the latest return %
  },
  "code": 1,
  "message": "stock successfully added"
}
```

**Failure Response:**

```json
{
  "data": {},
  "code": 0,
  "message": "stock fail to be added"
}
```

### 🔹 API: `deleteWatchListItem`

**Description:**

- Delete portfolio for user

**Method:** `DELETE`
**Endpoint:** `/api/v1/watchlists/{userId}/{ticker}`
**Success Response:**

```json
{
  "code": 1,
  "message": "stock successfully deleted"
}
```

**Failure Response:**

```json
{
  "code": 0,
  "message": "Stock successfully removed from watchlist"
}
```
