# tests/conftest.py
import pytest
import os

@pytest.fixture(scope="session")
def create_test_disk_image():
    """
    Creates a 10MB file and plants known files inside it for testing.
    This is the "test drive" for the carver.
    """
    image_path = "test_drive.img"
    image_size = 10 * 1024 * 1024  # 10 MB

    # Create dummy files to plant
    with open("test.txt", "w") as f:
        f.write("This is a test file for Project Phoenix.")
    # Create a dummy jpg (use a real small one)

    with open(image_path, "wb") as f:
        f.write(b'\0' * image_size) # Fill with zeros
        
        # Plant the text file at offset 1MB
        f.seek(1 * 1024 * 1024)
        with open("test.txt", "rb") as src:
            f.write(src.read())

        # Plant a known JPG at offset 5MB
        # ...

    yield image_path # This provides the path to the tests

    # Teardown: clean up the created files
    os.remove(image_path)
    os.remove("test.txt")