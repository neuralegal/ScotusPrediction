from fastai.text import *
import pandas as pd

#This function runs one instance of K trainings and saves the model predictions for that instance in a csv.
#Continues training until a prior training is better than the current then returns the best accuracy.
def kfold(ident,k,dataframe, path, learn_rate, data_lm,encoder,testingset,trainingset,dropout=0.3,bs=30):
	
	accuracylist = []
	
	data_clas = (TextDataBunch.from_df(path, train_df=trainingset, valid_df=testingset, vocab=data_lm.vocab, bs = bs))
	learn = text_classifier_learner(data_clas, AWD_LSTM, drop_mult=dropout)
	learn.load_encoder(encoder)
	learn.freeze()

	learn.fit_one_cycle(1, learn_rate, moms=(0.8,0.7))
	zero = learn.validate()
	zero = float(zero[1])
	learn.save("0")
	accuracylist.append(zero)
	
	learn.freeze_to(-2)
	learn.fit_one_cycle(1, slice(1e-2/(2.6**4),1e-2), moms=(0.8,0.7))
	first = learn.validate()
	first = float(first[1])
	learn.save("1")
	accuracylist.append(first)
	
	learn.freeze_to(-3)
	learn.fit_one_cycle(1, slice(5e-3/(2.6**4),5e-3), moms=(0.8,0.7))
	second = learn.validate()
	second = float(second[1])
	learn.save('2')
	accuracylist.append(second)

	learn.unfreeze()
	for i in range(3,22):
		learn.fit_one_cycle(1, slice(1e-3/(2.6**4),1e-3), moms=(0.8,0.7))
		accuracy = learn.validate()
		accuracy = float(accuracy[1])
		accuracylist.append(accuracy)
		learn.save(i)
			
	maxaccuracy = max(accuracylist)
	maxindex = accuracylist.index(maxaccuracy)
	learn.load(maxindex) #Loads weights from best performing epoch

	#Make predictions CSVs
	#loads testingset; gets model predictions on testingset
	df = testingset
	train = df.iloc[:,1].as_matrix()
	label = df.iloc[:,0].as_matrix()
	docket = df.iloc[:,2].as_matrix()
	
	data = []
	for i,text in enumerate(train): 
	#Creates DF with model predictions
		prediction = learn.predict(text)
		pred_outcome = prediction[1].item()
		accuracy = round(prediction[2][1].item(),3)
		outcome = label[i]
		doc = docket[i] 
		data.append([pred_outcome,outcome,accuracy,text,doc])
	
	maxed = round(maxaccuracy, 4)
	df = pd.DataFrame(data)
	
	#Does accuracy correction on DF. For each prediction pair (petitioner,respondent) takes more only the moer confident prediction where model predicts 
	#that both petitioner and respondent win or that both lose. This adjustment was only used for the Justice DFs.
	colnames = ["pred_outcome","outcome","accuracy","text","docket"]
	df.columns = colnames
	df['correctedprediction'] = df['pred_outcome']
	accuracylast = 0
	docketlast = ""

	for i,row in df.iterrows():
		if i > 1:
			curacc = df.iloc[i]["accuracy"]
			lastacc = df.iloc[i-1]["accuracy"]
			curpred = df.iloc[i]["pred_outcome"]
			lastpred = df.iloc[i-1]["pred_outcome"]
			curdoc = df.iloc[i]["docket"]
			lastdoc = df.iloc[i-1]["docket"]
			
			if curdoc == lastdoc:
				if curpred + lastpred == 2:
					if curacc > lastacc:
						df.at[i,"correctedprediction"] = 1
						df.at[i-1,"correctedprediction"] = 0
					else:
						df.at[i,"correctedprediction"] = 0
						df.at[i-1,"correctedprediction"] = 1
				
				if curpred + lastpred == 0:
					if curacc > lastacc:
						df.at[i,"correctedprediction"] = 1
						df.at[i-1,"correctedprediction"] = 0
					else:
						df.at[i,"correctedprediction"] = 0
						df.at[i-1,"correctedprediction"] = 1
	
	
	#Gets accuracy before adjustment
	correct = 0
	incorrect = 0

	for i,row in df.iterrows():
		if row["pred_outcome"] == row["outcome"]:
			correct += 1
		else:
			incorrect +=1
	total = correct+incorrect
	meanPRE = round(correct/total, 4)
	
	#Gets accuracy after adjustment.
	correct = 0
	incorrect = 0

	for i,row in df.iterrows():
		if row["correctedprediction"] == row["outcome"]:
			correct += 1
		else:
			incorrect +=1

	total = correct+incorrect
	meanPOST = round(correct/total, 4)
	
	df.to_csv(f"{ident}_{dataframe}_{k}_{maxed}_{meanPRE}__{meanPOST}_predictions.csv", sep=',', header=False,index=False, encoding = "utf-8")

	return
