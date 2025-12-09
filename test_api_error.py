import requests
import sys

def test_error():
    url = "http://localhost:8000/analyze"
    # Sending a bad ticker to trigger the 400 error
    payload = {"ticker": "INVALID TICKER WITH SPACES"} 
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 400:
            try:
                data = response.json()
                print(f"Parsed JSON detail: {data.get('detail')}")
            except:
                print("Could not parse JSON")
        else:
            print("Did not get expected 400 error.")
            
    except requests.exceptions.ConnectionError:
        print("Could not connect to localhost:8000. Is the server running?")

if __name__ == "__main__":
    test_error()
