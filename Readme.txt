This project uses an ensemble with an LSTM RNN and AdaBoost to predict Supreme Court outcomes from oral argument questions. 

--------------------
Scraping

The files used to scrape oyez.com and generate the training datasets are in the Scrape & Clean Data folder. We include our final datasets so repeating this step is unnecessary. To reproduce our scraping process, run the files in this order:

1) scrapeoyez.py
2) fill_in_advocates.py (adds info missed on first pass)
3) create_main_df.py
4) create_justice_dfs.py

Scraping Oyez takes several days. These files require Python 3, Pandas, BeautifulSoup, and Selenium

--------------------
Train LSTM

To train the LSTM, first open the Jupyter Notebook in the Train LSTM folder called Create Language Model.ipynb to create the language model. Training one up to our accuracy took several days on a GeForce GTX 1080. Next use Train LSTM Classifier.ipynb to train the main DF and the justices DFs. The language model needs to be trained before the classifier will work and was not included due to file size considerations. These files require fast.ai 1.0.48.

--------------------
Train Ensemble Model

To integrate the ensemble model, first use the EvaluateModel.ipynb notebook to add the softmax outputs from the model predictions to feature_table.csv (already added in inculded feature-table.csv) Then run neuralegal_adaboost.py in the main directory. This file requires Python 2.7 and Scikit-learn 0.17.1

-------------------
Check AUC Scores

Accuracy and AUC scores can be checked using EvaluateModel.ipynb.
