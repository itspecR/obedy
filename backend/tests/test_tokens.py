from accounts.tokens import hash_token, new_token


def test_tokens_are_long_and_unique():
    tokens = {new_token() for _ in range(100)}

    assert len(tokens) == 100
    assert all(len(token) >= 43 for token in tokens)


def test_hash_is_sha256_hex_and_deterministic():
    token = new_token()

    assert hash_token(token) == hash_token(token)
    assert len(hash_token(token)) == 64
    assert hash_token(token) != token
