h1 python3 DiscoveryAppln.py -l 10 -P 3 -S 2 > discovery.out 2>&1 &
h2 python3 PublisherAppln.py -l 10 -d "10.0.0.1:5555" -a "10.0.0.2" -n pub1 > pub1.out 2>&1 &
h3 python3 PublisherAppln.py -l 10 -d "10.0.0.1:5555" -a "10.0.0.3" -T 5 -n pub2 > pub2.out 2>&1 &
h4 python3 PublisherAppln.py -l 10 -d "10.0.0.1:5555" -a "10.0.0.4" -T 5 -n pub3 > pub3.out 2>&1 &
h5 python3 SubscriberAppln.py -l 10 -d "10.0.0.1:5555" -T 4 -n sub1 > sub1.out 2>&1 &
h6 python3 SubscriberAppln.py -l 10 -d "10.0.0.1:5555" -T 5 -n sub2 > sub2.out 2>&1 &
