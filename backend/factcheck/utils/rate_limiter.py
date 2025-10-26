
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, List, Any, Optional
from dataclasses import dataclass
from factcheck.utils.logger import CustomLogger

logger = CustomLogger(__name__).getlog()


@dataclass
class APIKeyStats:
    """Statistics for a single API key."""
    key_id: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rate_limit_hits: int = 0
    last_request_time: float = 0
    tokens: float = 0


class MultiKeyRateLimitedExecutor:

    def __init__(
        self,
        api_keys: List[str],
        max_requests_per_minute: int = 10, 
        max_requests_per_day: int = 250, 
        max_workers: int = 5, 
        request_window: int = 60,
        burst_size: Optional[int] = None,
    ):

        if not api_keys:
            raise ValueError("At least one API key must be provided")
        
        self.api_keys = api_keys
        self.num_keys = len(api_keys)
        self.max_requests_per_minute = max_requests_per_minute
        self.max_requests_per_day = max_requests_per_day
        self.max_workers = max_workers
        self.request_window = request_window
        self.burst_size = burst_size or max_requests_per_minute
        
        # Token bucket per API key
        self.refill_rate = max_requests_per_minute / request_window
        
        # Initialize stats for each key
        self.key_stats = {
            key: APIKeyStats(
                key_id=f"key_{i}",
                tokens=float(self.burst_size),
                last_request_time=time.time()
            )
            for i, key in enumerate(api_keys)
        }
        

        self.daily_usage = {key: 0 for key in api_keys}
        self.last_reset_date = self._get_current_date()
        
        # Thread synchronization
        self.lock = threading.Lock()
        self.key_available = threading.Condition(self.lock)
        
        # Round-robin index for key selection
        self.current_key_index = 0
        
        # Global statistics
        self.total_requests = 0
        self.total_wait_time = 0.0
        self.start_time = time.time()
    
    def _get_current_date(self) -> str:
        """Get current date in Pacific Time (for daily quota reset)."""
        import datetime
        import pytz
        
        # Get current time in Pacific timezone
        pacific = pytz.timezone('US/Pacific')
        now = datetime.datetime.now(pacific)
        return now.strftime('%Y-%m-%d')
    
    def _reset_daily_quotas_if_needed(self):
        """Reset daily quotas at midnight Pacific Time (called with lock held)."""
        current_date = self._get_current_date()
        
        if current_date != self.last_reset_date:
            logger.info(f"Daily quota reset: {self.last_reset_date} → {current_date}")
            self.daily_usage = {key: 0 for key in self.api_keys}
            self.last_reset_date = current_date
    
    def _refill_tokens(self, key: str):
        """Refill tokens for a specific API key (called with lock held)."""
        stats = self.key_stats[key]
        current_time = time.time()
        elapsed = current_time - stats.last_request_time
        
        # Add tokens based on elapsed time
        tokens_to_add = elapsed * self.refill_rate
        stats.tokens = min(self.burst_size, stats.tokens + tokens_to_add)
        stats.last_request_time = current_time
    
    def _find_available_key(self) -> Optional[str]:
        """
        Find an API key with available quota (called with lock held).
        Uses round-robin to distribute load evenly.
        
        Returns:
            API key string or None if all keys exhausted
        """
        self._reset_daily_quotas_if_needed()
        
        # Try all keys starting from current index
        for offset in range(self.num_keys):
            idx = (self.current_key_index + offset) % self.num_keys
            key = self.api_keys[idx]
            
            # Check daily quota
            if self.daily_usage[key] >= self.max_requests_per_day:
                logger.debug(f"{self.key_stats[key].key_id} daily quota exhausted")
                continue
            
            # Refill tokens
            self._refill_tokens(key)
            
            # Check if tokens available
            if self.key_stats[key].tokens >= 1.0:
                self.current_key_index = (idx + 1) % self.num_keys
                return key
        
        return None
    
    def _acquire_token(self) -> tuple[str, float]:
        """
        Acquire a token from any available API key.
        Blocks if no keys have tokens available.
        
        Returns:
            Tuple of (api_key, wait_time)
        """
        wait_start = time.time()
        
        with self.key_available:
            while True:
                # Try to find available key
                key = self._find_available_key()
                
                if key is not None:
                    # Token available - consume it
                    stats = self.key_stats[key]
                    stats.tokens -= 1.0
                    stats.total_requests += 1
                    self.daily_usage[key] += 1
                    self.total_requests += 1
                    
                    wait_time = time.time() - wait_start
                    self.total_wait_time += wait_time
                    
                    if wait_time > 0.1:
                        logger.debug(
                            f"{stats.key_id} acquired after {wait_time:.2f}s wait "
                            f"(tokens: {stats.tokens:.1f}, daily: {self.daily_usage[key]}/{self.max_requests_per_day})"
                        )
                    
                    return key, wait_time
                
                min_wait = float('inf')
                for key in self.api_keys:
                    if self.daily_usage[key] < self.max_requests_per_day:
                        stats = self.key_stats[key]
                        tokens_needed = 1.0 - stats.tokens
                        wait_time = max(0, tokens_needed / self.refill_rate)
                        min_wait = min(min_wait, wait_time)
                
                if min_wait == float('inf'):
                  
                    self.key_available.wait(timeout=300)
                    continue
                self.key_available.wait(timeout=min(min_wait + 0.1, 1.0))
    
    def _release_token_notification(self):
        """Notify waiting threads that time has passed."""
        with self.key_available:
            self.key_available.notify_all()
    
    def map(
        self, 
        func: Callable[[Any, str], Any],
        items: List[Any]
    ) -> List[Any]:
        """
        Execute function on all items with multi-key rate limiting.
        
        Args:
            func: Function to execute. Must accept (item, api_key) as parameters
            items: List of items to process
            
        Returns:
            List of results in same order as items
        """
        if not items:
            return []
        
        results = [None] * len(items)
        completed_count = 0
        lock = threading.Lock()
        
        # Track per-key statistics
        key_request_counts = {key: 0 for key in self.api_keys}
        
        def _wrapped_func(index, item):
            """Wrapper that enforces rate limiting and provides API key."""
            nonlocal completed_count
            
            # Acquire token (blocks if needed)
            api_key, wait_time = self._acquire_token()
            
            try:
                # Track which key is being used
                with lock:
                    key_request_counts[api_key] += 1
                
                # Execute the actual function with API key
                logger.debug(
                    f"Processing item {index + 1}/{len(items)} "
                    f"with {self.key_stats[api_key].key_id}..."
                )
                result = func(item, api_key)
                
                # Update stats
                self.key_stats[api_key].successful_requests += 1
                
                with lock:
                    completed_count += 1
                    elapsed = time.time() - self.start_time
                    rate = completed_count / elapsed if elapsed > 0 else 0
                    
                    # Show key distribution every 10 requests
                    if completed_count % 10 == 0:
                        key_dist = ", ".join([
                            f"{self.key_stats[k].key_id}:{key_request_counts[k]}"
                            for k in self.api_keys
                        ])
                        logger.info(
                            f"{completed_count}/{len(items)} "
                            f"({rate:.1f} req/s) | Keys: {key_dist}"
                        )
                
                return index, result
                
            except Exception as e:
                self.key_stats[api_key].failed_requests += 1
                logger.error(f"Task {index + 1} failed with {self.key_stats[api_key].key_id}: {e}")
                return index, None
            finally:
                # Notify other threads
                self._release_token_notification()

        self.start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [
                executor.submit(_wrapped_func, i, item)
                for i, item in enumerate(items)
            ]
            
            # Collect results
            for future in as_completed(futures):
                try:
                    index, result = future.result()
                    results[index] = result
                except Exception as e:
                    logger.error(f"Future failed: {e}")

        total_time = time.time() - self.start_time
        avg_wait = self.total_wait_time / self.total_requests if self.total_requests > 0 else 0
        actual_rate = len(items) / total_time if total_time > 0 else 0
        
        logger.info(
            f"   - Total items: {len(items)}\n"
            f"   - Total time: {total_time:.2f}s\n"
            f"   - Throughput: {actual_rate:.2f} req/s ({actual_rate * 60:.1f} req/min)\n"
            f"   - Avg wait: {avg_wait:.2f}s per request\n"
            f"   - Workers: {self.max_workers}\n"
        )
        for key in self.api_keys:
            stats = self.key_stats[key]
            logger.info(
                f"   {stats.key_id}: "
                f"{stats.successful_requests} success, "
                f"{stats.failed_requests} failed, "
                f"daily: {self.daily_usage[key]}/{self.max_requests_per_day}"
            )
        
        return results
    
    def get_stats(self) -> dict:
        """Get comprehensive statistics."""
        with self.lock:
            return {
                "total_requests": self.total_requests,
                "total_wait_time": self.total_wait_time,
                "num_keys": self.num_keys,
                "key_stats": {
                    stats.key_id: {
                        "total_requests": stats.total_requests,
                        "successful": stats.successful_requests,
                        "failed": stats.failed_requests,
                        "daily_usage": self.daily_usage[key],
                        "current_tokens": stats.tokens,
                    }
                    for key, stats in self.key_stats.items()
                },
            }

class RateLimitedExecutor:
    """
    Single-key rate limiter (legacy version).
    For new code, use MultiKeyRateLimitedExecutor instead.
    """
    
    def __init__(
        self,
        max_requests_per_minute: int = 10,
        max_workers: int = 4,
        request_window: int = 60,
        burst_size: Optional[int] = None,
    ):
        
        self.max_requests_per_minute = max_requests_per_minute
        self.max_workers = max_workers
        self.request_window = request_window
        self.burst_size = burst_size or max_requests_per_minute
        
        self.tokens = float(self.burst_size)
        self.max_tokens = float(self.burst_size)
        self.refill_rate = max_requests_per_minute / request_window
        self.last_refill_time = time.time()
        
        self.lock = threading.Lock()
        self.token_available = threading.Condition(self.lock)
        
        self.total_requests = 0
        self.total_wait_time = 0.0
    
    def _refill_tokens(self):
        """Refill tokens based on elapsed time."""
        current_time = time.time()
        elapsed = current_time - self.last_refill_time
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.max_tokens, self.tokens + tokens_to_add)
        self.last_refill_time = current_time
    
    def _acquire_token(self) -> float:
        """Acquire a token (blocks if needed)."""
        wait_start = time.time()
        
        with self.token_available:
            while True:
                self._refill_tokens()
                
                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    self.total_requests += 1
                    wait_time = time.time() - wait_start
                    self.total_wait_time += wait_time
                    return wait_time
                
                tokens_needed = 1.0 - self.tokens
                wait_time = tokens_needed / self.refill_rate
                self.token_available.wait(timeout=min(wait_time + 0.1, 1.0))
    
    def map(self, func: Callable, items: List[Any]) -> List[Any]:
        """Execute function on items with rate limiting."""
        if not items:
            return []
        
        results = [None] * len(items)
        
        def _wrapped_func(index, item):
            self._acquire_token()
            try:
                result = func(item)
                return index, result
            except Exception as e:
                logger.error(f"Task {index + 1} failed: {e}")
                return index, None
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(_wrapped_func, i, item) for i, item in enumerate(items)]
            for future in as_completed(futures):
                try:
                    index, result = future.result()
                    results[index] = result
                except Exception as e:
                    logger.error(f"Future failed: {e}")
        
        return results