from __future__ import division
import sklearn.pipeline
import sklearn.preprocessing
import sklearn.feature_selection
import sklearn.ensemble
import sklearn.grid_search
import sklearn.cross_validation
import sklearn.linear_model
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
import os
import csv

pd.options.mode.chained_assignment = None
NESTIMATORS = 10000
np.set_printoptions(threshold='nan')
search_parameters = {}

def main():
	infile = '.\\Dataframes\\feature_table.csv'

	feature_names = ['amicus', 'neuralegal_resp', 'neuralegal_pet', 'cutoffs_ALL', 'cutoffs_BREYER', 'cutoffs_GINSBURG', 
	'cutoffs_KENNEDY', 'cutoffs_SCALIA', 'GINSBURG_res_questions', 'ROBERTS_res_questions', 'SCALIA_res_questions', 
	'GINSBURG_pet_questions', 'KENNEDY_pet_questions', 'ROBERTS_pet_questions', 'SCALIA_pet_questions', 'BREYER_question_diff', 
	'GINSBURG_question_diff', 'KENNEDY_question_diff', 'ROBERTS_cc_ratio_pet', 'SCALIA_cc_ratio_pet', 'ROBERTS_cc_ratio_res', 'SCALIA_cc_ratio_res', 
	'KENNEDY_qc_ratio_diff', 'SCALIA_qc_ratio_diff', 'BREYER_wc_ratio_diff', 'GINSBURG_wc_ratio_diff', 'KENNEDY_wc_ratio_diff', 'SCALIA_wc_ratio_diff']

	decided_cases = pd.read_csv(infile, sep=',', index_col=0, encoding = "ISO-8859-1")
	gs_cases = decided_cases[feature_names].values.astype(np.float)
	gs_results = sklearn.preprocessing.LabelEncoder().fit_transform(decided_cases.winner)
	
	trees_model = sklearn.ensemble.ExtraTreesClassifier(n_jobs=-1, min_samples_leaf=5, max_depth=3, max_features=None,
		min_weight_fraction_leaf=0, n_estimators=NESTIMATORS, min_samples_split=2, criterion='gini',
		bootstrap=True)

	ada_boost_model = sklearn.ensemble.AdaBoostClassifier(trees_model, n_estimators=NESTIMATORS)

	# Create the cross-validation fold
	cv = sklearn.cross_validation.KFold(len(gs_cases), n_folds=10, shuffle=False)

	# Create grid searcher
	grid_search = sklearn.grid_search.GridSearchCV( sklearn.ensemble.AdaBoostClassifier(trees_model, n_estimators=NESTIMATORS), search_parameters,
		 cv=cv, verbose=1,n_jobs=-1)

	# Fit model in grid search
	model = grid_search.fit(gs_cases, gs_results)

	print(model.grid_scores_)
	print(model.best_estimator_)
	print model.best_estimator_.feature_importances_
	print("Test accuracy score: %0.2f%%" % (model.best_score_ * 100))
	
	with open ("neuralegal.csv", 'w') as csvfile:
		csv_writer = csv.writer(csvfile);
		csv_writer.writerow(["Docket", "Majority Votes", "Predicted", "Actual"])
		for train_index, test_index in cv:
			model = ada_boost_model.fit(gs_cases[train_index], gs_results[train_index])
			results = model.predict(gs_cases[test_index])
			for i in range(len(test_index)):
				 csv_writer.writerow([decided_cases.index[test_index[i]], decided_cases['majVotes'][test_index[i]],	 results[i],  gs_results[test_index][i]])

	return# model.best_score_

if __name__ == '__main__':
	main()