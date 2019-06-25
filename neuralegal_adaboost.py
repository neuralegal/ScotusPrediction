import sklearn.ensemble
import sklearn.preprocessing
from sklearn.model_selection import KFold
from sklearn.model_selection import GridSearchCV
import numpy as np
import pandas as pd
import csv

search_parameters = {}
file = '.\\Dataframes\\feature_table.csv'
n_estimators = 10000

def main():
	features = ['amicus', 'neuralegal_resp', 'neuralegal_pet', 'cutoffs_ALL', 'cutoffs_BREYER', 'cutoffs_GINSBURG', 
	'cutoffs_KENNEDY', 'cutoffs_SCALIA', 'GINSBURG_res_questions', 'ROBERTS_res_questions', 'SCALIA_res_questions', 
	'GINSBURG_pet_questions', 'KENNEDY_pet_questions', 'ROBERTS_pet_questions', 'SCALIA_pet_questions', 'BREYER_question_diff', 
	'GINSBURG_question_diff', 'KENNEDY_question_diff', 'ROBERTS_cc_ratio_pet', 'SCALIA_cc_ratio_pet', 'ROBERTS_cc_ratio_res', 
	'SCALIA_cc_ratio_res', 'KENNEDY_qc_ratio_diff', 'SCALIA_qc_ratio_diff', 'BREYER_wc_ratio_diff', 'GINSBURG_wc_ratio_diff', 
	'KENNEDY_wc_ratio_diff', 'SCALIA_wc_ratio_diff']

	df = pd.read_csv(file, index_col=0)
	cases = df[features].values.astype(np.float)
	results = sklearn.preprocessing.LabelEncoder().fit_transform(df.winner)

	trees_model = sklearn.ensemble.ExtraTreesClassifier(n_jobs=-1, min_samples_leaf=5, max_depth=3, max_features=None,
		min_weight_fraction_leaf=0, n_estimators=n_estimators, min_samples_split=2, criterion='gini',
		bootstrap=True)

	#Fit AdaBoost
	ada_boost_model = sklearn.ensemble.AdaBoostClassifier(trees_model, n_estimators=n_estimators)

	#KFold
	cv = KFold(n_splits=10) 

	#Grid search to report feature performance
	grid_search = GridSearchCV(sklearn.ensemble.AdaBoostClassifier(trees_model, n_estimators=n_estimators), search_parameters,
		 cv=cv, verbose=1,n_jobs=-1,iid=False)
	model = grid_search.fit(cases, results)

	print("Feature Importances: \n",model.best_estimator_.feature_importances_)
	print(f"Test Accuracy: {(model.best_score_ * 100)}%")

	with open ("ensemble predictions.csv", 'w') as csvfile:
		csv_writer = csv.writer(csvfile);
		csv_writer.writerow(["Docket", "Majority Votes", "Predicted", "Actual"])
		for train_index, test_index in cv.split(cases):
			model = ada_boost_model.fit(cases[train_index], results[train_index])
			test = model.predict(cases[test_index])
			for i in range(len(test_index)):
				csv_writer.writerow([df.index[test_index[i]], df['majVotes'][test_index[i]],test[i], results[test_index][i]])
				
if __name__ == '__main__':
	main()
