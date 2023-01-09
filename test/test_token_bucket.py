import unittest
from unittest import mock
import gc

from common.token_bucket import TokenBucket, TokenBucketPool


class TokenBucketTestCase(unittest.TestCase):

  @mock.patch('time.time')
  def test_new_bucket(self, mock_time):
    mock_time.return_value = 0
    
    # 10 tokens every 10 seconds
    bucket = TokenBucket(None, max_tokens=10, time_window_secs=1)
    assert not bucket.consume(10.01)

    assert bucket.consume(10) # remaining is 0 after
    assert not bucket.consume(.01)
  
  @mock.patch('time.time')
  def test_partially_filled_bucket(self, mock_time):
    mock_time.return_value = 0
    
    # 10 tokens every 10 seconds
    bucket = TokenBucket(None, max_tokens=10, time_window_secs=1)
    # Empty the bucket
    bucket.consume(10)
    assert not bucket.consume(.001)
    
    # Test partially filled bucket
    mock_time.return_value = 0.7
    assert not bucket.consume(8)
    assert bucket.consume(7)

  @mock.patch('time.time')
  def test_long_interval_limit(self, mock_time):
    mock_time.return_value = 0
    
    # 10 tokens every 10 seconds
    bucket = TokenBucket(None, max_tokens=10, time_window_secs=1)
    # Empty the bucket
    bucket.consume(10)
    assert not bucket.consume(.001)
    
    # Test that we only have max_tokens after a long interval
    mock_time.return_value = 100
    assert not bucket.consume(10.01)
    assert bucket.consume(10)
  
  @mock.patch('time.time')
  def test_constant_rate_polling(self, mock_time):
    mock_time.return_value = 0
    
    # 10 tokens every 10 seconds
    bucket = TokenBucket(None, max_tokens=10, time_window_secs=1)

    # mimic 1 token per 0.1s (10 req/s) - it should never run out
    for i in range(1000):
      mock_time.return_value = i/10
      assert bucket.consume(1)
  
  def test_token_bucket_pool(self):
    pool = TokenBucketPool(1, 10)

    bucket1 = pool.get('key1')
    bucket2 = pool.get('key1')
    bucket3 = pool.get('key3')
    assert bucket1 == bucket2
    assert bucket1 != bucket3

    # delete refs to bucket 1 & 2, the GC -> should create a new bucket for key1
    bucket1_str = repr(bucket1)
    del bucket1, bucket2
    gc.collect()
    bucket4 = pool.get('key1')
    assert repr(bucket4) != bucket1_str


