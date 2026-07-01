import pytest
from app.infrastructure.proxy.load_balancer import RoundRobinLoadBalancer

def test_round_robin():
    targets = ["key1", "key2", "key3"]
    lb = RoundRobinLoadBalancer(targets)
    
    assert lb.get_next() == "key1"
    assert lb.get_next() == "key2"
    assert lb.get_next() == "key3"
    assert lb.get_next() == "key1"
