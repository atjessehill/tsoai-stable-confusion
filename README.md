# the Synchronizer
a system that synchronizes to the rhythm of a drummer in real time.

## What is it?
This AI [model](https://en.wikipedia.org/wiki/Variable-order_Markov_model) will listen to a human drummer to learn their rhythms, and will proceed to predict 
when the next drum hit will occur. This results in a synchronization between both human and machine.

We have integrated this model into a performance environment where multiple musicians can share the same model,
where all connected users can train the model with their own rhythms, as well as receive the predictions
the model generates.

For more information please see our [presentation](https://docs.google.com/presentation/d/1RtAwKZlJBGq9dZS6AOp_USvlXLBZsO0zyNzY5rle4fg/edit#slide=id.g2e6eccc813b_1_94). 

## Setup
```
# Python setup
cd server
pip install -r requirements.txt
python server.py

# Max client setup
1. Open up the nvm/demo.maxpat
2. script npm install (first time only)
3. script start
```


## About
This project was developed as part of The Sound of AI x UPF MTG Generative AI workshop, and was a result of 
collaboration between musicians and technologists:

- [Atser Damsma](https://www.linkedin.com/in/atser-damsma-12b52661/)
- [Daphne Xanthopoulou](https://www.linkedin.com/in/daphne-xanthopoulou-26b336278/)
- [Jesse Hill](https://www.linkedin.com/in/jessehillcs/)
- [Weilu Ge](geweilu.com)