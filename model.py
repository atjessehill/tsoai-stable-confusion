'''
PPM Method-C with interpolated smoothing, see p89 of [1].

[1] Pearce, M. T. (2005). The construction and evaluation of statistical models
of melodic structure in music perception and composition (Doctoral dissertation,
City University London).

'''
import numpy as np
from pynput import keyboard
import time 
from collections import defaultdict, OrderedDict
from scipy.stats import norm
import matplotlib.pyplot as plt
import threading


DEFAULT_MAX_ORDER = 2

## Just trying a change

class PPMC(object):
    ''' PPM Method-C, using interpolated smoothing '''

    RESULT_HEADERS = ('PDF','Alphabet','AlphabetIntervals')
    
    def __init__(self, order, alphabet,modelSD,maxSD,learnRatio):
        self.order = order
        self.alphabet = sorted(alphabet)
        print('sorted alphabet:', self.alphabet)
        self.alpha_len = len(self.alphabet)

        # Context -> Count of Subsequent (for alphabet)
        self.contexts = defaultdict(lambda: np.zeros(self.alpha_len))
        self.rowNames = self.alphabet
        self.sd = modelSD
        self.maxSD = maxSD
         # mapping from letters (keys) to time intervals, which will be udpated on the fly
        self.alphabetInterval = {}
        self.learnRatio = learnRatio
        self.fullSequenceCategories = []
        
    def informationcontent(self, pdf, e):
        return -np.log2(pdf[self.alpha_map[e]])

    def entropy(self, pdf):
        return -np.sum(pdf*np.log2(pdf))

    def normalise(self, pdf):
        return pdf/pdf.sum()
    
    def sum_of_gaussians(self,x, means, std_devs, probabilities):
        ''' Returns sum of multiple normal distributions ''' 
        # Check if the input arrays are valid
        if len(means) != len(std_devs) or len(means) != len(probabilities):
            raise ValueError("All input arrays must have the same length.")
        probabilities = np.array(probabilities)
        # Calculate the sum of weighted Gaussian distributions
        sum_gaussians = np.zeros_like(x, dtype=float)
        for mean, std_dev, prob in zip(means, std_devs, probabilities):
            sum_gaussians += prob * norm.pdf(x, loc=mean, scale=std_dev)
        return sum_gaussians

    def pdf_for(self, ctx, normalise=True):
        pdf = self._smoothed_pdf(ctx)
        return self.normalise(pdf) if normalise else pdf
    
    def number_to_letter(self,number):
        return chr(number + 64)

    def add_alphabet(self,evt):
        '''  we encountered a new category, so we add it to the alphabet
        ## the interval corresponding to alphabet item will be evt ''' 
        alphLen = len(self.alphabet) # get length of current alphabet
        curLetter = self.number_to_letter(alphLen+1)
        print('new category is:', curLetter)
        # add to alphabet
        self.alphabetInterval[curLetter] = evt
        self.alphabet = np.append(self.alphabet,curLetter)
        return curLetter

    def update_alphabet(self,evt,key):
        ''' change the interval value of category key by averaging the previous 
            interval value with the new interval''' 
        closest =  self.alphabetInterval[key]
        avgEvt = round((self.learnRatio*evt+(1-self.learnRatio)*closest),5) # replace by the average between the old, close evt and the new evt
        # replace value at key
        self.alphabetInterval[key] = avgEvt
        
    def categorize(self,evt):
        '''  Calculate the distance (in SDs) from the event to items in alphabet ''' 
        numSDAlphabet = self.alphabet.copy() # copying alphabet to replace with SDs
        for enc in range(len(self.alphabet)):## now calculate the probability of the evt for items in alphabet
            alphaItem = self.alphabet[enc]
            curAlphInterval = self.alphabetInterval[alphaItem] # get interval value from alphabet dictionary
            numSD = abs(evt-curAlphInterval)/(curAlphInterval*self.sd)
            numSDAlphabet[enc] = numSD
        if len(self.alphabet)>0: # non-empty alphabet
            ## now calculate the probability of the alphabet item given the event
            minSDs = min(numSDAlphabet)
            print('Checking whether I have anything that looks like this interval in memory...')
            maxIndex = np.where(numSDAlphabet==minSDs)
            maxIndex = maxIndex[0]
            maxIndex = int(maxIndex[0])
            curCategory = self.alphabet[maxIndex]
        else:
            print('empty alphabet')
            minSDs = 10 #this is a bit hacky
        if (float(minSDs) < self.maxSD): ## FOUND A CLOSE ITEM IN MEMORY
            print('I have a close enough item in memory (',curCategory,'), at a distance of',minSDs,'standard deviations')
            self.update_alphabet(evt,curCategory)
        else: ## THIS IS REALLY A NEW EVENT
            print('It really seems new, I will add it to my alphabet!')
            # add to alphabet
            curCategory = self.add_alphabet(evt)
            # update alphamap
            # Mapping from alpha to numeric ordinals, and inverse, for sanity
            self.alpha_map = OrderedDict((a, i) for i, a in enumerate(self.alphabet))
            self.alpha_map_inv = OrderedDict((i, a) for a, i in self.alpha_map.items())
            # add another row to the counts in self.context
            for key in self.contexts:
                self.contexts[key] = np.append(self.contexts[key], 0)
            # update the length of the alphabet
            self.alpha_len = len(self.alphabet)

        return curCategory
            
    def fit(self, evt, verbose=False):
        ''' Train on complete sequence, in ngrams bounded by self.order '''
        # get the current context from the full sequence
        from_ind, to_ind = max(0, len(self.fullSequenceCategories)-self.order), len(self.fullSequenceCategories)
        print("_____________________")
        print('Current interval:',evt)
        # Record surprisal for upcoming symbol (evt), given context (ctx)
        ctx= self.fullSequenceCategories[from_ind:to_ind]
        evtCategory = self.categorize(evt) # categorize the new event
        self.fullSequenceCategories.append(evtCategory)
        print('alphabet after categorization:',self.alphabet)
        if len(self.fullSequenceCategories) == 1:
            sequenceCategories = tuple(evtCategory)
            print(sequenceCategories)
        else:
            sequenceCategories = tuple(ctx) + tuple(evtCategory)

        pdf = self.pdf_for(sequenceCategories, normalise=True)
        curAlphabetIntervals = list(self.alphabetInterval.values())            
        # Recursively update counts of context (for all orders within bound),
        # e.g. [A,B,R]->A:  []->A, [R]->A, [B,R]->A, [A,B,R]->A
        for j in reversed(range(0, min(to_ind+1,self.order+1))): 
            subseq = sequenceCategories[j:len(sequenceCategories)]
            ctx, evt = subseq[:-1], subseq[-1]
            if len(self.contexts[ctx]) == 0:
                self.contexts[ctx] = np.zeros(len(self.alphabet))
            self.contexts[ctx][self.alpha_map[evt]] += 1
        return pdf,self.alphabet,curAlphabetIntervals

    def _smoothed_pdf(self, ctx):
        ''' Interpolated smoothing to derive unnormalised PDF for context '''
        if ctx is None:
            # Base case
            observed_alpha = np.count_nonzero(self.contexts[()])
            base_prob = 1.0 / (self.alpha_len + 1 - observed_alpha)
            pdf = np.ones(self.alpha_len) * base_prob
        else:
            # Find the symbols occurring after this context
            subsequent = self.contexts[ctx]
            subseq_set = np.count_nonzero(subsequent)
            total_subsequent = subsequent.sum()

            # Interpolated probabilities
            if total_subsequent:
                # Weighting function
                lam_s = total_subsequent / (total_subsequent + subseq_set)
                # Maximum likelihood estimate
                A = lam_s * self.contexts[ctx]/total_subsequent
            else:
                # Avoid divide by zero errors
                lam_s = 0.0
                A = np.zeros(self.alpha_len)
            suffix = ctx[1:] if len(ctx) > 0 else None
            B = (1.0 - lam_s) * self._smoothed_pdf(suffix)
            pdf = A + B
        return pdf
    
    def delayed_message(self,delay,category, velocity):
        velocity = round(velocity*127)
        time.sleep(delay)
        print(f"MESSAGE: Interval: {delay}  -  Category {category}  - Velocity: {velocity}")
        ## Send these values to Max

if __name__ == '__main__':
    #########################
    ### parameters
    order = 4 # was 4
    noisePar = 0.2 # was 0.18 # determines SD
    learnRatio = 0.1 # was 0.1
    minQuantizationProb = 0.7 # determines threshold probability for which item will be put in category
    maxSD = 2 # 2.5 worked well

    alphabet = set([]) ## Initialize empty alphabet
    #onsettimes = np.array([0,1,,3,3.55,4,5,6,7])
    #iois = np.array([1,2,3,1,2.1,2.99,1,2,3,1,2,3])
    ppm = PPMC(order=order,alphabet=alphabet,modelSD = noisePar,maxSD = maxSD,learnRatio=learnRatio)    
    print("Press G to start. Press 'Esc' to exit.")

    last_time = None
    start_time = time.time()
    # Create an array that will contain the full prediction since the first tap
    # currently 300 s (5 minutes)
    masterPrediction = np.zeros(300000)

    def on_press(key):
        global last_time
        global firstTapTime
        try:
            if key.char == 'g':  # Check for spacebar
                current_time = time.time()
                if last_time is not None:
                    timeFromFirstTap = current_time-firstTapTime
                    print('Time since first tap:',timeFromFirstTap)
                    interval = current_time - last_time
                    interval = round(interval,3)
                    print(f"Time interval: {interval:.4f} seconds")
                    pdf,alphabet,curAlphabetIntervals = ppm.fit(interval,verbose=True)
                    print('pdf:',np.round(pdf,2))
                    print('alphabet:',alphabet)
                    print('curAlphabetIntervals',np.round(curAlphabetIntervals,2))
                    
                    # send message at the right time after tap
                    # Create a new timer that calls delayed_message after 2 seconds
                    for interval in range(0,len(alphabet)):
                        curCat = alphabet[interval]
                        curInterval = curAlphabetIntervals[interval]
                        curVelocity = pdf[interval]
                        timingTrig = threading.Timer(curInterval, ppm.delayed_message, args=(curInterval,curCat,curVelocity,))
                        timingTrig.start()
                                    
                    # calculate sum of gaussians
                    # first make a time array
                    start = 0
                    stop = 10  # in seconds
                    step = 1 / 1000  # 1 ms = 1/1000 seconds
                    t = np.arange(start, stop + step, step) # Define a range of x values
                    sumProb = ppm.sum_of_gaussians(t, np.round(curAlphabetIntervals,3), np.round(curAlphabetIntervals,3)*noisePar, pdf)
                    plt.plot(t, sumProb, label='Sum of Gaussians')
                    plt.xlabel('Time from tap (s)')
                    plt.ylabel('Probability')
                    plt.title('Sum of Weighted Gaussian Distributions')
                    plt.show()
                else:
                    firstTapTime = time.time()
                    print(f"First key press detected at time {firstTapTime}")

                last_time = current_time
        except AttributeError:
            # Handle special keys
            pass
    
    def on_release(key):
        if key == keyboard.Key.esc:
            # Stop listener
            print("Exiting...")
            return False
    
    # Collect events until released
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

