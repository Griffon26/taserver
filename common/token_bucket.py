import time
from weakref import WeakValueDictionary


class TokenBucketPool:
    """ Helper class to manage in-use token buckets. This allows us to share a rate limit across
        multiple connections from the same IP/user for example, automatically creating and GC-ing 
        them as needed.
    """

    def __init__(self, max_tokens: int, time_window_secs: float, unit: str = 'tokens'):
        self.buckets = WeakValueDictionary()
        self.max_tokens = max_tokens
        self.time_window_secs = time_window_secs
        self.unit = unit

    def get(self, key):
        if key in self.buckets:
            bucket = self.buckets[key]
        else:
            bucket = TokenBucket(key, self.max_tokens, self.time_window_secs, self.unit)
            self.buckets[key] = bucket
        return bucket


class TokenBucket:
    """
    Token bucket algorithm used for rate limiting traffic/requests.
    Each bucket receives max_tokens number of tokens per time_window_sec, but never has more than
    max_tokens.
    Calling consume(requested_tokens) checks if there are enough tokens remaining, and subtracts the
    requested tokens from the remaining tokens.
    """

    def __init__(self, key, max_tokens: int, time_window_secs: float, unit: str = 'tokens'):
        self.key = key
        self.max_tokens = max_tokens
        self.time_window_secs = time_window_secs
        self.unit = unit
        self.remaining_tokens = max_tokens
        self.last_call_time = time.time()

    def consume(self, requested_tokens) -> bool:
        """
        Check whether a request has enough tokens to proceed. If there are enough tokens, the 
        requested number of tokens are removed from the remaining tokens.

            Returns:
                bool: whether the request has enough tokens to continue
        """

        # first, refill the tokens based on the time since the last consume()
        now = time.time()
        elapsed = (now - self.last_call_time)
        new_tokens = (elapsed / self.time_window_secs) * self.max_tokens
        # Add the new tokens, restrict the total remaining to the max
        self.remaining_tokens = min(self.max_tokens, self.remaining_tokens + new_tokens)
        self.last_call_time = now
        #print(f"\t {self} remaining {self.remaining_tokens} {self.unit}")
        if requested_tokens > self.remaining_tokens:
            return False
        else:
            self.remaining_tokens -= requested_tokens
            return True

    def __str__(self) -> str:
        return f'{self.max_tokens} {self.unit}/{self.time_window_secs} secs for {self.key}'
