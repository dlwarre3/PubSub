###############################################
#
# Author: Aniruddha Gokhale
# Vanderbilt University
#
# Purpose: Skeleton/Starter code for the Discovery application
#
# Created: Spring 2023
#
###############################################


# This is left as an exercise for the student.  The Discovery service is a server
# and hence only responds to requests. It should be able to handle the register,
# is_ready, the different variants of the lookup methods. etc.
#
# The key steps for the discovery application are
# (1) parse command line and configure application level parameters. One
# of the parameters should be the total number of publishers and subscribers
# in the system.
# (2) obtain the discovery middleware object and configure it.
# (3) since we are a server, we always handle events in an infinite event loop.
# See Publisher code to see how the event loop is written. Accordingly, when a
# message arrives, the middleware object parses the message and determines
# what method was invoked and then hands it to the application logic to handle it
# (4) Some data structure or in-memory database etc will need to be used to save
# the registrations.
# (5) When all the Publishers and subscribers in the system have registered with us,
# then we are in a ready state and will respond with a true to is_ready method. Until then
# it will be false.


# import the needed packages
import os     # for OS functions
import sys    # for syspath and system exception
import time   # for sleep
import argparse # for argument parsing
import configparser # for configuration parsing
import logging # for logging. Use it in place of print statements.

# Now import our CS6381 Middleware
from CS6381_MW.DiscoveryMW import DiscoveryMW
# We also need the message formats to handle incoming responses.
from CS6381_MW import discovery_pb2

# import any other packages you need.
from enum import Enum  # for an enumeration we are using to describe what state we are in

##################################
#       DiscoveryAppln class
##################################
class DiscoveryAppln ():

  class State (Enum):
    INITIALIZE = 0,
    CONFIGURE = 1,
    IDLE = 2,
    REGISTER = 3,
    ISREADY = 4

  ########################################
  # constructor
  ########################################
  def __init__ (self, logger):
    self.state = self.State.INITIALIZE # state that are we in
    self.name = None # our name (some unique name)
    self.publishers = {} # dictionary of publishers
    self.pubcount = 0 # number of publishers
    self.subscribers = {} # dictionary of subscribers
    self.brokercount = 0
    self.broker = {} # dictionary of brokers
    self.subcount = 0 # number of subscribers
    self.lookup = None # one of the diff ways we do lookup
    self.dissemination = None # direct or via broker
    self.mw_obj = None # ha    self.broker = {} # dictionary of brokers
    self.subcount = 0 # number of subscribersndle to the underlying Middleware object
    self.logger = logger  # internal logger for print statements
    

  ########################################
  # configure/initialize
  ########################################
  def configure (self, args):
    ''' Initialize the object '''

    try:
      # Here we initialize any internal variables
      self.logger.info ("DiscoveryAppln::configure")

      # set our current state to CONFIGURE state
      self.state = self.State.CONFIGURE
      
      # initialize our variables
      self.name = args.name # our name
      self.pubcount = args.publishers
      self.subcount = args.subscribers
      self.brokercount = args.brokers

      # Now, get the configuration object
      self.logger.debug ("DiscoveryAppln::configure - parsing config.ini")
      config = configparser.ConfigParser ()
      #config.read (args.config)
      #self.lookup = config["Discovery"]["Strategy"]
    
      # Now setup up our underlying middleware object to which we delegate
      # everything
      self.logger.debug ("DiscoveryAppln::configure - initialize the middleware object")
      self.mw_obj = DiscoveryMW (self.logger)
      self.mw_obj.configure (args) # pass remainder of the args to the m/w object
      
      self.logger.info ("DiscoveryAppln::configure - configuration complete")
      
    except Exception as e:
      raise e

  ########################################
  # driver program
  ########################################
  def driver (self):
    ''' Driver program '''

    try:
      self.logger.info ("DiscoveryAppln::driver")

      # dump our contents (debugging purposes)
      self.dump ()

      # First ask our middleware to keep a handle to us to make upcalls.
      # This is related to upcalls. By passing a pointer to ourselves, the
      # middleware will keep track of it and any time something must
      # be handled by the application level, invoke an upcall.
      self.logger.debug ("DiscoveryAppln::driver - upcall handle")
      self.mw_obj.set_upcall_handle (self)

      
      self.mw_obj.event_loop (timeout=0)  # start the event loop
      
      self.logger.info ("DiscoveryAppln::driver completed")
      
    except Exception as e:
      raise e

  ########################################
  # generic invoke method called as part of upcall
  #
  # This method will get invoked as part of the upcall made
  # by the middleware's event loop after it sees a timeout has
  # occurred.
  ########################################
  def invoke_operation (self):
    ''' Invoke operating depending on state  '''

    try:
      self.logger.info ("DiscoveryAppln::invoke_operation" + str(self.state))

      # check what state are we in. If we are in REGISTER state,
      # we send register request to discovery service. If we are in
      # ISREADY state, then we keep checking with the discovery
      # service.
      if (self.state == self.State.REGISTER):
        # notify middleware to await registration requests of publishers and subscribers
        self.logger.debug ("DiscoveryAppln::invoke_operation - register publishers and subcribers")
        self.mw_obj.register_response ()

        # Remember that we were invoked by the event loop as part of the upcall.
        # So we are going to return back to it for its next iteration. Because
        # we have just now sent a register request, the very next thing we expect is
        # to receive a response from remote entity. So we need to set the timeout
        # for the next iteration of the event loop to a large num and so return a None.
        return None
      
      elif (self.state == self.State.ISREADY):
        # Now keep checking to see if we are finished registering and ready to go
        
        self.logger.debug ("DiscoveryAppln::invoke_operation - check if are ready to go")
        # self.mw_obj.is_ready_response (True)  # send the is_ready? response

        # Remember that we were invoked by the event loop as part of the upcall.
        # So we are going to return back to it for its next iteration. Because
        # we have just now sent a isready request, the very next thing we expect is
        # to receive a response from remote entity. So we need to set the timeout
        # for the next iteration of the event loop to a large num and so return a None.
        return None
      elif (self.state == self.State.IDLE):
        return

      
    except Exception as e:
      raise e


  ########################################
  # handle isready request method called as part of upcall
  ########################################
  def isready_request (self, isready_req):
    ''' handle isready request '''
    self.logger.info ("DiscoveryAppln::handling isready_request")
    try:
      
      self.state = self.State.ISREADY
      # Once all publishers and subcribers are registered and accounted for in dictionaries, send ready response
      if (str(len(self.publishers)) == str(self.pubcount)):
        self.logger.info ("DiscoveryAppln TRUE::pub ready is " + str(len(self.publishers)) + "pub count is " + str(self.pubcount)) 
        if (str(len(self.subscribers)) == str(self.subcount)):
          self.logger.info ("DiscoveryAppln TRUE::sub ready is " + str(len(self.subscribers)) + "sub count is " + str(self.subcount))
          if (str(len(self.broker)) == str(self.brokercount)):
            self.logger.info ("DiscoveryAppln TRUE::broker ready is " + str(len(self.broker)) + "sub count is " + str(self.brokercount))
            self.mw_obj.is_ready_response(True)
          else:
            self.logger.info ("DiscoveryAppln FALSE::broker ready is " + str(len(self.broker)) + "sub count is " + str(self.subscribers)) 
            self.mw_obj.is_ready_response(False)

        else:
          self.logger.info ("DiscoveryAppln FALSE::sub ready is " + str(len(self.subscribers)) + "sub count is " + str(self.subcount)) 
          self.mw_obj.is_ready_response(False)


      else:
        self.logger.info ("DiscoveryAppln FALSE::pub ready is " + str(len(self.publishers)) + "pub count is " + str(self.pubcount)) 
        self.logger.info ("DiscoveryAppln FALSE::sub ready is " + str(len(self.subscribers)) + "sub count is " + str(self.subcount)) 
        self.logger.info ("DiscoveryAppln FALSE::broker ready is " + str(len(self.broker)) + "sub count is " + str(self.subscribers)) 
        self.mw_obj.is_ready_response(False)
        
      # return timeout of 0 so event loop calls us back in the invoke_operation
      # method, where we take action based on what state we are in.
      return 0
    
    except Exception as e:
      raise e

  ########################################
  # handle register request method called as part of upcall
  ########################################
  def register_request (self, disc_req):
    ''' handle register_request request '''

    try:
      self.logger.debug ("DiscoveryAppln::register_request - " + str(disc_req))

      if (disc_req.register_req.role == discovery_pb2.ROLE_PUBLISHER):
        self.publishers.update({disc_req.register_req.info.id: disc_req.register_req})
      elif (disc_req.register_req.role == discovery_pb2.ROLE_SUBSCRIBER):
        self.subscribers.update({disc_req.register_req.info.id: disc_req.register_req})
      elif (disc_req.register_req.role == discovery_pb2.ROLE_BOTH):
        self.broker.update({disc_req.register_req.info.id: disc_req.register_req})
      self.mw_obj.register_response()
      # return timeout of 0 so event loop calls us back in the invoke_operation
      # method, where we take action based on what state we are in.
      return 0
    
    except Exception as e:
      raise e

  ########################################
  # handle publisher lookup by topic request as part of upcall
  ########################################
  def lookup_pub_bytopic_request (self, disc_req):
    ''' handle lookup_pub_bytopic request '''

    try:
      self.logger.debug ("DiscoveryAppln::lookup_pub_bytopic_req - " + str(disc_req))
      self.logger.debug ("DiscoveryAppln::publishers - " + str(self.publishers))
      lookupResult = []
      for publisher in self.publishers:
        for topic in disc_req.lookup_req.topiclist:  
          self.logger.debug ("DiscoveryAppln::lookup_pub_bytopic_req - looking for publisher with topic" + str(topic) + " in list " + str(self.publishers[publisher].topiclist))
          if (topic in self.publishers[publisher].topiclist):
            lookupResult.append(self.publishers[publisher].info)

      self.logger.debug ("DiscoveryAppln::lookup_pub_bytopic_req - sending lookupResult - " + str(lookupResult))
      self.mw_obj.lookup_pub_bytopic_response(lookupResult)
      # return timeout of 0 so event loop calls us back in the invoke_operation
      # method, where we take action based on what state we are in.
      return None
    
    except Exception as e:
      raise e

  
  ########################################
  # handle publisher lookup by topic request as part of upcall
  ########################################
  def lookup_all_pub_request (self, disc_req):
    ''' handle lookup_all_pub_request request '''

    try:
      self.logger.debug ("DiscoveryAppln::lookup_all_pub_request - " + str(disc_req))
      self.logger.debug ("DiscoveryAppln::publishers - " + str(self.publishers))
      lookupResult = []
      for publisher in self.publishers:
        lookupResult.append(self.publishers[publisher].info)

      self.logger.debug ("DiscoveryAppln::lookup_all_pub_request - sending lookupResult - " + str(lookupResult))
      self.mw_obj.lookup_all_pub_response(lookupResult)
      # return timeout of 0 so event loop calls us back in the invoke_operation
      # method, where we take action based on what state we are in.
      return None
    
    except Exception as e:
      raise e

  ########################################
  # handle publisher lookup by topic request as part of upcall
  ########################################
  def lookup_broker_request (self, disc_req):
    ''' handle lookup_pub_bytopic request '''

    try:
      self.logger.debug ("DiscoveryAppln::lookup_broker_request - " + str(disc_req))
      self.logger.debug ("DiscoveryAppln::broker - " + str(self.broker))

      for broker in self.broker:
        self.mw_obj.lookup_broker_response(self.broker[broker])
      # return timeout of 0 so event loop calls us back in the invoke_operation
      # method, where we take action based on what state we are in.
      return None
    
    except Exception as e:
      raise e

  ########################################
  # dump the contents of the object 
  ########################################
  def dump (self):
    ''' Pretty print '''

    try:
      self.logger.info ("**********************************")
      self.logger.info ("DiscoveryAppln::dump")
      self.logger.info ("------------------------------")
      self.logger.info ("     Name: {}".format (self.name))
      self.logger.info ("     Lookup: {}".format (self.lookup))
      self.logger.info ("     Subscriber count: {}".format (self.subcount))
      self.logger.info ("     Subscribers: {}".format (self.subscribers))
      self.logger.info ("     Publisher count: {}".format (self.pubcount))
      self.logger.info ("     Publishers: {}".format (self.publishers))
      self.logger.info ("     Broker count: {}".format (self.brokercount))
      self.logger.info ("     Broker: {}".format (self.broker))
      self.logger.info ("**********************************")

    except Exception as e:
      raise e

###################################
#
# Parse command line arguments
#
###################################
def parseCmdLineArgs ():
  # instantiate a ArgumentParser object
  parser = argparse.ArgumentParser (description="Discovery Application")
  
  # Now specify all the optional arguments we support
  # At a minimum, you will need a way to specify the IP and port of the lookup
  # service, the role we are playing, what dissemination approach are we
  # using, what is our endpoint (i.e., port where we are going to bind at the
  # ZMQ level)
  
  parser.add_argument ("-n", "--name", default="disc", help="Some name assigned to us. Keep it unique per Discovery")

  parser.add_argument ("-a", "--addr", default="10.0.0.1", help="IP addr of this Discovery to advertise (default: localhost)")

  parser.add_argument ("-p", "--port", type=int, default=5555, help="Port number on which our underlying Discovery ZMQ service runs, default=5555")

  parser.add_argument ("-B", "--brokers", default="0", help="Number of brokers (default: 0)")

  parser.add_argument ("-P", "--publishers", default="0", help="Number of publishers (default: 0)")

  parser.add_argument ("-S", "--subscribers", default="0", help="Number of subscribers (default: 0)")

  parser.add_argument ("-l", "--loglevel", type=int, default=logging.DEBUG, choices=[logging.DEBUG,logging.INFO,logging.WARNING,logging.ERROR,logging.CRITICAL], help="logging level, choices 10,20,30,40,50: default 20=logging.INFO")
  
  return parser.parse_args()


###################################
#
# Main program
#
###################################
def main ():
  try:
    # obtain a system wide logger and initialize it to debug level to begin with
    logging.info ("Main - acquire a child logger and then log messages in the child")
    logger = logging.getLogger ("DiscoveryAppln")
    
    # first parse the arguments
    logger.debug ("Main: parse command line arguments")
    args = parseCmdLineArgs ()

    # reset the log level to as specified
    logger.debug ("Main: resetting log level to {}".format (args.loglevel))
    logger.setLevel (args.loglevel)
    logger.debug ("Main: effective log level is {}".format (logger.getEffectiveLevel ()))

    # Obtain a Discovery application
    logger.debug ("Main: obtain the Discovery appln object")
    disc_app = DiscoveryAppln (logger)

    # configure the object
    logger.debug ("Main: configure the Discovery appln object")
    disc_app.configure (args)

    # now invoke the driver program
    logger.debug ("Main: invoke the Discovery appln driver")
    disc_app.driver ()

  except Exception as e:
    logger.error ("Exception caught in main - {}".format (e))
    return

    
###################################
#
# Main entry point
#
###################################
if __name__ == "__main__":

  # set underlying default logging capabilities
  logging.basicConfig (level=logging.DEBUG,
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


  main ()

