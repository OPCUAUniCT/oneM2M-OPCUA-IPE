from threading import Thread, Event 



class StoppableThread(Thread): 

    # Thread class with a _stop() method.  
    #Stoppable thread class used to monitored value when data-cache not used
  
    def __init__(self, group=None, target=None, name=None, 
        args=(), kwargs=None, *, daemon=None):
        Thread.__init__(self, group=group, target=target, name=name, args=args, kwargs=kwargs)
        
        self._stop_me = Event() 
  
    # function using _stop function 
    def stop(self): 
        self._stop_me.set() 
  
    def stopped(self): 
        return self._stop_me.isSet() 
  
    def run(self): 
        while True: 
            if self.stopped(): 
                return
            self._target(*self._args)
