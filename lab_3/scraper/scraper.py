def mock_scrape_cactus():
    """
    Mock version of scrape_cactus_phones() that returns test data
    without making actual HTTP requests
    """
    mock_products = [
        {   
            "id": 0,
            "name": "Laptop Apple MacBook PRO 16\" MNW93",
            "price": {
                "MDL": 63269.0
            },
            "specifications": "2023"
        },
        {
            "id": 1,
            "name": "Laptop Apple MacBook PRO 16\" MNW83",
            "price": {
                "MDL": 48839.0
            },
            "specifications": "2023"
        },
        {
            "id": 2,
            "name": "Laptop Apple MacBook PRO 14\" MPHE3",
            "price": {
                "MDL": 48284.0
            },
            "specifications": "2023"
        },
        {
            "id": 3,
            "name": "Laptop Apple MacBook PRO 14 MPHG3",
            "price": {
                "MDL": 72926.0
            },
            "specifications": "2023"
        },
        {
            "id": 4,
            "name": "Laptop Apple MacBook PRO 16\" MNWE3",
            "price": {
                "MDL": 78809.0
            },
            "specifications": "2023"
        },
        {
            "id": 5,
            "name": "Laptop Apple MacBook PRO 16 MNWA3",
            "price": {
                "MDL": 77477.0
            },
            "specifications": "2023"
        },
        {
            "id": 6,
            "name": "Laptop Apple MacBook PRO 14 MPHK3",
            "price": {
                "MDL": 72926.0
            },
            "specifications": "2023"
        },
        {
            "id": 7,
            "name": "Laptop Apple MacBook Air 15\" MQKT3",
            "price": {
                "MDL": 32633.0
            },
            "specifications": "2023"
        },
        {
            "id": 8,
            "name": "Laptop Apple MacBook Air 15\" MQKR3",
            "price": {
                "MDL": 28304.0
            },
            "specifications": "2023"
        },
        {
            "id": 9,
            "name": "Laptop Apple MacBook Air 15\" MQKP3",
            "price": {
                "MDL": 28359.0
            },
            "specifications": "2023"
        },
        {
            "id": 10,
            "name": "Laptop Apple MacBook Air 15\" MQKQ3",
            "price": {
                "MDL": 32633.0
            },
            "specifications": "2023"
        },
        {
            "id": 11,
            "name": "Laptop Apple MacBook Air 15\" MQKV3",
            "price": {
                "MDL": 32633.0
            },
            "specifications": "2023"
        },
        {
            "id": 12,
            "name": "Laptop Apple MacBook Air 15\" MQKU3",
            "price": {
                "MDL": 27749.0
            },
            "specifications": "2023"
        },
        {
            "id": 13,
            "name": "Laptop Apple MacBook Air 15\" MQKX3",
            "price": {
                "MDL": 31745.0
            },
            "specifications": "2023"
        },
        {
            "id": 14,
            "name": "Laptop Apple MacBook Air 15\" MQKW3",
            "price": {
                "MDL": 27749.0
            },
            "specifications": "2023"
        }
    ]

    print("Started mock scraping products")
    import time
    time.sleep(1)
    print("Finished the mock scraping")

    return mock_products