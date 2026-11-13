import requests

API_KEY = "vach_1ytE2CY5X2Eutz2kJuEYATYayNIttsj7svNDSrTXJiO48BVcFt7GRRoLbcpGXe4wzakUlG5vc7oIcrGddNRoeiRnwT752YbP_7e03d48ca3f27f9bc1db4df9c70560c7"

with open("test.wav", "rb") as f:   # change the filename if yours is .mp3 or .m4a
    r = requests.post(
        "https://api.vachana.ai/stt/v3",
        headers={"X-API-Key-ID": API_KEY},
        files={"audio_file": f},
        data={"language_code": "hi-IN"},
    )

print(r.status_code)
print(r.json())