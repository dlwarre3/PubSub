###############################################
#
# Author: Aniruddha Gokhale
# Vanderbilt University
#
# Purpose: Skeleton/Starter code for the discovery middleware code
#
# Created: Spring 2023
#
###############################################

# Designing the logic is left as an exercise for the student.
#
# The discovery service is a server. So at the middleware level, we will maintain
# a REP socket binding it to the port on which we expect to receive requests.
#
# There will be a forever event loop waiting for requests. Each request will be parsed
# and the application logic asked to handle the request. To that end, an upcall will need
# to be made to the application logic.


# import the needed packages
import os     # for OS functions
import sys    # for syspath and system exception
import time   # for sleep
import logging # for logging. Use it in place of print statements.
import zmq  # ZMQ sockets

# import serialization logic
from CS6381_MW import discovery_pb2
#from CS6381_MW import topic_pb2  # you will need this eventually

# import any other packages you need.

##################################
#       Discovery Middleware class
##################################
class DiscoveryMW ():

  ########################################
  # constructor
  ########################################
  def __init__ (self, logger):
    self.logger = logger  # internal logger for print statements
    self.rep = None # will be a ZMQ REP socket to talk to publishers and subscribers
    self.poller = None # used to wait on incoming replies
    self.addr = None # our advertised IP address
    self.port = None # port num where we are going to publish our topics
    self.upcall_obj = None # handle to appln obj to handle appln-specific data
    self.handle_events = True # in general we keep going thru the event loop

  ########################################
  # configure/initialize
  ########################################
  def configure (self, args):
    ''' Initialize the object '''

    try:
      # Here we initialize any internal variables
      self.logger.info ("DiscoveryMW::configure")

      # First retrieve our advertised IP addr and the publication port num
      self.port = args.port
      self.addr = args.addr
      
      # Next get the ZMQ context
      self.logger.debug ("DiscoveryMW::configure - obtain ZMQ context")
      context = zmq.Context ()  # returns a singleton object

      # get the ZMQ poller object
      self.logger.debug ("DiscoveryMW::configure - obtain the poller")
      self.poller = zmq.Poller ()
      
      # Now acquire the REP socket
      # REP is needed because we are the server of the Discovery service

      self.logger.debug ("DiscoveryMW::configure - obtain REQ and PUB sockets")
      self.rep = context.socket (zmq.REP)

      # Since are using the event loop approach, register the REP socket for incoming events
      self.logger.debug ("DiscoveryMW::configure - register the REP socket for incoming replies")
      self.poller.register (self.rep, zmq.POLLIN)
      self.logger.debug ("DiscoveryMW::configure - DONE register the REP socket for incoming replies")
      

      bind_string = "tcp://" + str(self.addr) + ":" + str(self.port)
      self.logger.debug ("DiscoveryMW::configure - DONE BIND STRING" + bind_string)
      self.rep.bind (bind_string)
      self.logger.debug ("DiscoveryMW::configure - DONE register the REP socket for incoming replies")
      self.logger.info ("DiscoveryMW::configure completed")

    except Exception as e:
      raise e

  #################################################################
  # run the event loop where we expect to receive a reply to a sent request
  #################################################################
  def event_loop (self, timeout=None):

    try:
      self.logger.info ("DiscoveryMW::event_loop - run the event loop")

      # we are using a class variable called "handle_events" which is set to
      # True but can be set out of band to False in order to exit this forever
      # loop
      while self.handle_events:  # it starts with a True value
        # poll for events. We give it an infinite timeout.
        # The return value is a socket to event mask mapping
        events = dict (self.poller.poll (timeout=timeout))

        # Unlike the previous starter code, here we are never returning from
        # the event loop but handle everything in the same locus of control
        # Notice, also that after handling the event, we retrieve a new value
        # for timeout which is used in the next iteration of the poll
        
        # check if a timeout has occurred. We know this is the case when
        # the event mask is empty
        if not events:
          # timeout has occurred so it is time for us to make appln-level
          # method invocation. Make an upcall to the generic "invoke_operation"
          # which takes action depending on what state the application
          # object is in.
          self.logger.info ("DiscoveryMW::event_loop - invoke_operation")
          timeout = self.upcall_obj.invoke_operation ()
          
        elif self.rep in events:  # this is the only socket on which we should be receiving replies
          self.logger.info ("DiscoveryMW::event_loop - handling request")
          # handle the incoming request from remote entity and return the result
          timeout = self.handle_request ()
          
        else:
          raise Exception ("Unknown event after poll")
    except Exception as e:
      raise e
    self.logger.debug ("DiscoveryMW::event_loop - out of the event loop")
  #################################################################
  # handle an incoming discovery request
  #################################################################
  def handle_request (self):

    try:
      self.logger.info ("DiscoveryMW::handle_reply")

      # let us first receive all the bytes
      bytesRcvd = self.rep.recv ()

      # now use protobuf to deserialize the bytes
      # The way to do this is to first allocate the space for the
      # message we expect, here DiscoveryReq and then parse
      # the incoming bytes and populate this structure (via protobuf code)
      disc_req = discovery_pb2.DiscoveryReq ()
      disc_req.ParseFromString (bytesRcvd)
      self.logger.info ("DiscoveryMW::handle_reply" + str(disc_req))

      # demultiplex the message based on the message type but let the application
      # object handle the contents as it is best positioned to do so. See how we make
      # the upcall on the application object by using the saved handle to the appln object.
      #
      # Note also that we expect the return value to be the desired timeout to use
      # in the next iteration of the poll.
      if (disc_req.msg_type == discovery_pb2.TYPE_REGISTER):
        # let the appln level object decide what to do
        timeout = self.upcall_obj.register_request (disc_req)
      elif (disc_req.msg_type == discovery_pb2.TYPE_ISREADY):
        # this is a response to is ready request
        timeout = self.upcall_obj.isready_request (disc_req)
      elif (disc_req.msg_type == discovery_pb2.TYPE_LOOKUP_PUB_BY_TOPIC):
        timeout = self.upcall_obj.lookup_pub_bytopic_request (disc_req)
      elif (disc_req.msg_type == discovery_pb2.TYPE_LOOKUP_ALL_PUBS):
        timeout = self.upcall_obj.lookup_all_pub_request (disc_req)
      elif (disc_req.msg_type == discovery_pb2.TYPE_LOOKUP_BROKER):
        timeout = self.upcall_obj.lookup_broker_request (disc_req)

      else: # anything else is unrecognizable by this object
        # raise an exception here
        raise ValueError ("Unrecognized response message")

      return timeout
    
    except Exception as e:
      raise e
            
  def is_ready_response (self, ready_status):
    ''' register the appln with the discovery service '''

    try:
      self.logger.info ("DiscoveryMW::is_ready_response")

      # we do a similar kind of serialization as we did in the register
      # message but much simpler as the message format is very simple.
      # Then send the request to the discovery service
    
      # The following code shows serialization using the protobuf generated code.
      
      # first build a IsReady message
      self.logger.debug ("DiscoveryMW::is_ready - populate the nested IsReady msg")
      isready_resp = discovery_pb2.IsReadyResp ()  # allocate 
      isready_resp.status = ready_status
      self.logger.debug ("DiscoveryMW::is_ready - done populating nested IsReady msg " + str(isready_resp.status))
      # Build the outer layer Discovery Message
      self.logger.debug ("DiscoveryMW::is_ready - build the outer DiscoveryReq message")
      disc_resp = discovery_pb2.DiscoveryResp ()
      disc_resp.msg_type = discovery_pb2.TYPE_ISREADY
      # It was observed that we cannot directly assign the nested field here.
      # A way around is to use the CopyFrom method as shown
      disc_resp.isready_resp.CopyFrom (isready_resp)
      self.logger.debug ("DiscoveryMW::is_ready - done building the outer message")
      
      # now let us stringify the buffer and print it. This is actually a sequence of bytes and not
      # a real string
      buf2send = disc_resp.SerializeToString ()
      self.logger.debug ("Stringified serialized buf = {}".format (buf2send))

      # now send this to our discovery service
      self.logger.debug ("DiscoveryMW::is_ready - send stringified buffer to Discovery service")
      self.rep.send (buf2send)  # we use the "send" method of ZMQ that sends the bytes
      
      # now go to our event loop to receive a response to this request
      self.logger.info ("DiscoveryMW::is_ready - response sent " + str(disc_resp))
      
    except Exception as e:
      raise e
    
  ########################################
  # register with the discovery service
  ########################################
  def register_response (self):
    ''' register the appln with the discovery service '''

    try:
      self.logger.info ("PublisherMW::register")

      # first build a Register message
      self.logger.debug ("DiscoveryMW::register_response - populate the nested Register msg")
      register_resp = discovery_pb2.RegisterResp ()  # allocate 
      register_resp.status = discovery_pb2.STATUS_SUCCESS
      self.logger.debug ("DiscoveryMW::register_response - done populating nested Register msg")


      # Finally, build the outer layer DiscoveryReq Message
      self.logger.debug ("PublisherMW::register - build the outer DiscoveryReq message")
      disc_resp = discovery_pb2.DiscoveryResp ()  # allocate
      disc_resp.msg_type = discovery_pb2.TYPE_REGISTER  # set message type
      # It was observed that we cannot directly assign the nested field here.
      # A way around is to use the CopyFrom method as shown
      disc_resp.register_resp.CopyFrom (register_resp)
      self.logger.debug ("PublisherMW::register - done building the outer message")
      
      # now let us stringify the buffer and print it. This is actually a sequence of bytes and not
      # a real string
      buf2send = disc_resp.SerializeToString ()
      self.logger.debug ("Stringified serialized buf = {}".format (buf2send))

      # now send this to our discovery service
      self.logger.debug ("PublisherMW::register - send stringified buffer to Discovery service")
      self.rep.send (buf2send)  # we use the "send" method of ZMQ that sends the bytes

      # now go to our event loop to receive a response to this request
      self.logger.info ("PublisherMW::register - sent register message and now now wait for reply")
    
    except Exception as e:
      raise e

  ########################################
  # send list of publishers that match a certain topic
  ########################################
  def lookup_pub_bytopic_response (self, publisher):
    ''' send list of publishers that publish a certain topic '''

    try:
      self.logger.info ("DiscoveryMW::lookup_pub_bytopic_response")

      # first build a Register message
      self.logger.debug ("DiscoveryMW::lookup_pub_bytopic_response - populate the nested LookupPubByTopicResp msg")
      lookup_resp = discovery_pb2.LookupPubByTopicResp ()  # allocate 
      lookup_resp.info.extend(publisher)
      self.logger.debug ("DiscoveryMW::lookup_pub_bytopic_response - " + str(lookup_resp))
      self.logger.debug ("DiscoveryMW::lookup_pub_bytopic_response - done populating nested LookupPubByTopicResp msg")


      # Finally, build the outer layer DiscoveryReq Message
      self.logger.debug ("DiscoveryMW::lookup_pub_bytopic_response - build the outer DiscoveryReq message")
      disc_resp = discovery_pb2.DiscoveryResp ()  # allocate
      disc_resp.msg_type = discovery_pb2.TYPE_LOOKUP_PUB_BY_TOPIC  # set message type
      # It was observed that we cannot directly assign the nested field here.
      # A way around is to use the CopyFrom method as shown
      disc_resp.lookup_resp.CopyFrom (lookup_resp)
      self.logger.debug ("DiscoveryMW::lookup_pub_bytopic_response - done building the outer message")
      
      # now let us stringify the buffer and print it. This is actually a sequence of bytes and not
      # a real string
      buf2send = disc_resp.SerializeToString ()
      self.logger.debug ("Stringified serialized buf = {}".format (buf2send))

      # now send this to our REP socket
      self.logger.debug ("DiscoveryMW::lookup_pub_bytopic_response - send stringified buffer to REP socket")
      self.rep.send (buf2send)  # we use the "send" method of ZMQ that sends the bytes

      # now go to our event loop to receive a response to this request
      self.logger.info ("DiscoveryMW::lookup_pub_bytopic_response - sent publisher info")
    
    except Exception as e:
      raise e

  ########################################
  # send list of all publishers
  ########################################
  def lookup_all_pub_response (self, publisher):
    ''' send list of publishers that publish a certain topic '''

    try:
      self.logger.info ("DiscoveryMW::lookup_all_pub_response")

      # first build a Register message
      self.logger.debug ("DiscoveryMW::lookup_all_pub_response - populate the nested LookupPubByTopicResp msg")
      lookup_resp = discovery_pb2.LookupAllPubsResp ()  # allocate 
      lookup_resp.info.extend(publisher)
      self.logger.debug ("DiscoveryMW::lookup_all_pub_response - " + str(lookup_resp))
      self.logger.debug ("DiscoveryMW::lookup_all_pub_response - done populating nested LookupPubByTopicResp msg")


      # Finally, build the outer layer DiscoveryReq Message
      self.logger.debug ("DiscoveryMW::lookup_all_pub_response - build the outer DiscoveryReq message")
      disc_resp = discovery_pb2.DiscoveryResp ()  # allocate
      disc_resp.msg_type = discovery_pb2.TYPE_LOOKUP_ALL_PUBS  # set message type
      # It was observed that we cannot directly assign the nested field here.
      # A way around is to use the CopyFrom method as shown
      disc_resp.lookup_all_resp.CopyFrom (lookup_resp)
      self.logger.debug ("DiscoveryMW::lookup_all_pub_response - done building the outer message")
      
      # now let us stringify the buffer and print it. This is actually a sequence of bytes and not
      # a real string
      buf2send = disc_resp.SerializeToString ()
      self.logger.debug ("Stringified serialized buf = {}".format (buf2send))

      # now send this to our REP socket
      self.logger.debug ("DiscoveryMW::lookup_all_pub_response - send stringified buffer to REP socket")
      self.rep.send (buf2send)  # we use the "send" method of ZMQ that sends the bytes

      # now go to our event loop to receive a response to this request
      self.logger.info ("DiscoveryMW::lookup_all_pub_response - sent publisher info")

    except Exception as e:
      raise e

  ########################################
  # send list of all publishers
  ########################################
  def lookup_broker_response (self, broker):
    ''' send broker '''

    try:
      self.logger.info ("DiscoveryMW::lookup_broker_response")

      # first build a Register message
      self.logger.debug ("DiscoveryMW::lookup_broker_response - populate the nested LookupBrokerResp msg")
      lookup_resp = discovery_pb2.LookupBrokerResp ()  # allocate 
      lookup_resp.info.CopyFrom (broker.info)
      self.logger.debug ("DiscoveryMW::lookup_broker_response - " + str(lookup_resp))
      self.logger.debug ("DiscoveryMW::lookup_broker_response - done populating nested LookupBrokerResp msg")


      # Finally, build the outer layer DiscoveryReq Message
      self.logger.debug ("DiscoveryMW::lookup_broker_response - build the outer DiscoveryReq message")
      disc_resp = discovery_pb2.DiscoveryResp ()  # allocate
      disc_resp.msg_type = discovery_pb2.TYPE_LOOKUP_BROKER  # set message type
      # It was observed that we cannot directly assign the nested field here.
      # A way around is to use the CopyFrom method as shown
      disc_resp.broker_resp.CopyFrom (lookup_resp)
      self.logger.debug ("DiscoveryMW::lookup_broker_response - done building the outer message")
      
      # now let us stringify the buffer and print it. This is actually a sequence of bytes and not
      # a real string
      buf2send = disc_resp.SerializeToString ()
      self.logger.debug ("Stringified serialized buf = {}".format (buf2send))

      # now send this to our REP socket
      self.logger.debug ("DiscoveryMW::lookup_broker_response - send stringified buffer to REP socket")
      self.rep.send (buf2send)  # we use the "send" method of ZMQ that sends the bytes

      # now go to our event loop to receive a response to this request
      self.logger.info ("DiscoveryMW::lookup_broker_response - sent broker info")
    
    except Exception as e:
      raise e

  ########################################
  # set upcall handle
  #
  # here we save a pointer (handle) to the application object
  ########################################
  def set_upcall_handle (self, upcall_obj):
    ''' set upcall handle '''
    self.upcall_obj = upcall_obj

  ########################################
  # disable event loop
  #
  # here we just make the variable go false so that when the event loop
  # is running, the while condition will fail and the event loop will terminate.
  ########################################
  def disable_event_loop (self):
    ''' disable event loop '''
    self.handle_events = False

