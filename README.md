# PA1

For Milestone 1, I have completed the discovery application and service, along with the subscriber application and service up until dissemination of data via the discovery service.
My publishers and subscribers successfully register with the service and enter the respective DISSEMINATE and CONSUME state to begin processing data. I tested via the mininet shell code provided in the EXPERIMENTS folder. I have set up the skeletons for the subscriber CONSUME state to begin processing topics.


For milestone 2, subscribers are now able to subscribe on any and all publishers based on topic under direct dissemination. When provided multiple publishers, subscribers will consume topics for all publishers. When both publishers and subscribers register to the discovery service, their registrant info is held in a dictionary by the discovery service (this was from milestone 1). Using this, subscribers send a lookup pub by topic request to the discovery service, and the discovery service responds in a lookup pub by topic response with address and port information of all publishers that are disseminating topics of interest to a subscriber. The subscriber then uses setsockopt on its pub socket, connects to the addresses and ports provided and consumes data over these connections. 
