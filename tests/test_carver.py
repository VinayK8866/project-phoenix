# tests/test_carver.py
from phoenix_recovery.carver_engine import RawCarver
import hashlib

def test_carver_finds_known_file(create_test_disk_image):
    """
    Tests if the carver can find and correctly extract a file
    that was planted in our test disk image.
    """
    carver = RawCarver(source_path=create_test_disk_image)
    recovered_files = carver.scan()

    # Assert that one file was found
    assert len(recovered_files) == 1 

    # Assert that the recovered file's content is correct
    original_hash = hashlib.sha256(open("test.txt", "rb").read()).hexdigest()
    recovered_hash = hashlib.sha256(open(recovered_files[0], "rb").read()).hexdigest()
    
    assert original_hash == recovered_hash