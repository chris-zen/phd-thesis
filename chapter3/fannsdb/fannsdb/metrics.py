import random
import numpy as np
import pandas as pd
from sklearn.metrics import matthews_corrcoef, accuracy_score, f1_score, precision_score, recall_score, roc_curve, auc, confusion_matrix
import matplotlib.pyplot as plt

# metric functions

tp = lambda y_true, y_pred, tp, fp, fn, tn: tp
fp = lambda y_true, y_pred, tp, fp, fn, tn: fp
fn = lambda y_true, y_pred, tp, fp, fn, tn: fn
tn = lambda y_true, y_pred, tp, fp, fn, tn: tn

tpr = lambda y_true, y_pred, tp, fp, fn, tn: np.float64(tp) / (tp + fn)

#tpr = lambda y_true, y_pred, tp, fp, fn, tn: recall_score(y_true, y_pred)
tpr = lambda y_true, y_pred, tp, fp, fn, tn: np.float64(tp) / (tp + fn)

spc = lambda y_true, y_pred, tp, fp, fn, tn: np.float64(tn) / (fp + tn)

#ppv = lambda y_true, y_pred, tp, fp, fn, tn: precision_score(y_true, y_pred)
ppv = lambda y_true, y_pred, tp, fp, fn, tn: np.float64(tp) / (tp + fp)

f1 = lambda y_true, y_pred, tp, fp, fn, tn: f1_score(y_true, y_pred)

#acc = lambda y_true, y_pred, tp, fp, fn, tn: accuracy_score(y_true, y_pred)
acc = lambda y_true, y_pred, tp, fp, fn, tn: np.float64(tp + tn) / np.float64(
                                                         (tp + fn) + (fp + tn))

#mcc = lambda y_true, y_pred, tp, fp, fn, tn: matthews_corrcoef(y_true, y_pred)
mcc = lambda y_true, y_pred, tp, fp, fn, tn: (
                   np.float64(tp * tn - fp * fn) / np.sqrt(
                      np.float64(tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)))

score_fn = {
    "TP"         : tp,
    "FP"         : fp,
    "FN"         : fn,
    "TN"         : tn,
    "TPR"        : tpr, # Sensitivity, recall
    "SPC"        : spc, # Specificity
    "PPV"        : ppv, # Precision, Positive predictive value
    "F1"         : f1,
    "ACC"        : acc,
    "MCC"        : mcc
}

# performance calculation

def calc_perf(y_true, tset, cutoffs, perf, scores):
    
    tp = fp = fn = tn = np.nan

    #req_cm = len(set(scores) & set(["TPR", "SPC", "PPV", "ACC", "MCC"])) > 0    
	
    for i, cutoff in enumerate(cutoffs):
        y_pred = np.array(tset >= cutoff, dtype=np.int8)
    	
        #if req_cm:
        cm = confusion_matrix(y_true, y_pred)
        tp, fp, fn, tn = cm[0,0], cm[0,1], cm[1,0], cm[1,1]
    
        for j, score in enumerate(scores):
            v = score_fn[score](y_true, y_pred, tp, fp, fn, tn)
            perf[i,j] = v if np.isfinite(v) else 0.0

    return perf

def balanced_perf(pos, neg, cutoffs, scores, **kwargs):
    num_pos = len(pos.index)
    num_neg = len(neg.index)
    num_perf = len(scores)
    y_true = np.empty(num_pos + num_neg, np.int8)
    y_true[:num_pos] = 1
    y_true[num_pos:] = 0
    tset = pd.concat([pos, neg])

    #print(num_pos, num_neg, len(tset), len(y_true))
    perf = np.zeros((cutoffs.shape[0], num_perf))

    calc_perf(y_true, tset, cutoffs, perf[:,:], scores)

    fpr, tpr, thresholds = roc_curve(y_true, tset)
    auc_value = auc(fpr, tpr)

    perf = pd.DataFrame(perf, columns=scores, index=cutoffs)
    roc = pd.DataFrame({"FPR" : fpr, "TPR" : tpr, "thresholds" : thresholds})
    
    return (perf, roc, auc_value)

def undersampling_perf(pos, neg, cutoffs, scores, num_samples=None, **kwargs):
    num_pos = len(pos.index)
    num_neg = len(neg.index)
    num_perf = len(scores)
    y_true = np.empty(num_pos * 2, np.int8)
    y_true[:num_pos] = 1
    y_true[num_pos:] = 0
    
    num_partitions = int(num_neg / num_pos)
    num_samples = min(num_samples or num_partitions, num_partitions)
    
    #print("{} / {} = {} -> {}".format(num_neg, num_pos, num_partitions, num_samples))

    tset = np.zeros(num_pos * 2, np.int8)
    perf = np.empty((cutoffs.shape[0], num_perf, num_samples))
    for s in xrange(num_samples):
        nix = random.sample(neg.index, num_pos)
        neg_sample = neg.ix[nix]
        tset = pd.concat([pos, neg_sample])
        calc_perf(y_true, tset, cutoffs, perf[:,:,s], scores)
        #neg = neg.drop(nix)
	
    fpr, tpr, thresholds = roc_curve(y_true, tset)
    auc_value = auc(fpr, tpr)

    perf = pd.DataFrame(perf.mean(axis=2), columns=scores, index=cutoffs)
    roc = pd.DataFrame({"FPR" : fpr, "TPR" : tpr, "thresholds" : thresholds})
    
    return (perf, roc, auc_value)

def perf_metrics(data_path, predictors, undersampling=False, transforms=None,
                 title=None, scores=["MCC", "ACC"], class_column="ID",
                 pos_label="POS", neg_label="NEG", w=1/64.0,
                 cutoff_score="MCC", **kwargs):
                 
    if transforms is None:
        transforms = {}

    d = pd.read_csv(data_path, sep="\t", index_col=False)
    pos = d[d[class_column] == pos_label]
    neg = d[d[class_column] == neg_label]

    results = dict(
        title=title,
        predictors=predictors,
        metrics={})

    for i, pred in enumerate(predictors):
        results["metrics"][pred] = m = {}

        p = pos[pred][np.isfinite(pos[pred])]
        n = neg[pred][np.isfinite(neg[pred])]
        
        if len(p) == 0 or len(n) == 0:
	        continue

        if pred in transforms:
            transform = transforms[pred]
            p = p.map(transform)
            n = n.map(transform)

        p.sort()
        n.sort()
        
        rmin = min(p.min(), n.min())
        rmax = max(p.max(), n.max())
        cutoffs = np.arange(rmin, rmax + w * 2.0, w)
        num_cutoffs = len(cutoffs)

        num_pos = len(p.index)
        num_neg = len(n.index)
    
        if undersampling and num_neg > num_pos:
            perf, roc, auc_value = undersampling_perf(p, n, cutoffs, scores, **kwargs)
        else:
            perf, roc, auc_value = balanced_perf(p, n, cutoffs, scores, **kwargs)
        
        #from IPython.display import display
        #display(perf)
        
        best_perf = perf.max(axis=0)
        best_perf_cutoff = perf.idxmax(axis=0)
        best_perf_index = { name : perf.index.get_loc(idx) for name, idx in best_perf_cutoff.iteritems()}
        cutoff = best_perf_cutoff[cutoff_score]

        m.update(
            rmin=rmin, rmax=rmax,
            cutoffs=cutoffs.tolist(),
            perf=perf.to_dict("list"),
            best_perf=best_perf.to_dict(),
            best_perf_cutoff=best_perf_cutoff.to_dict(),
            best_perf_index=best_perf_index,
            roc=roc.to_dict("list"),
            auc=auc_value)

        #nhist, nbins = np.histogram(n, bins=num_cutoffs)
        nhist, nbins = np.histogram(n, bins=cutoffs)
        nmax = float(nhist.max()) #if len(nhist) > 0 else 0	
        ncumhist = np.cumsum(nhist)
        ncummax = float(ncumhist[-1])
        ncumdist = ncumhist / ncummax
        ncutoffidx = np.argmin(np.abs(nbins[:-1] - cutoff))
        m.update(
            neg_hist=nhist.tolist(),
            neg_bins=nbins.tolist(),
            neg_cumhist=ncumhist.tolist(),
            neg_cummax=ncummax,
            neg_cumdist=ncumdist.tolist(),
            neg_cutoff_index=ncutoffidx)

        #phist, pbins = np.histogram(p, bins=num_cutoffs)
        phist, pbins = np.histogram(p, bins=cutoffs)
        pmax = float(phist.max())
        pcumhist = np.cumsum(phist)
        pcummax = float(pcumhist[-1])
        pcumdist = pcumhist / pcummax
        pcutoffidx = np.argmin(np.abs(pbins[:-1] - cutoff))
        m.update(
            pos_hist=phist.tolist(),
            pos_bins=pbins.tolist(),
            pos_cumhist=pcumhist.tolist(),
            pos_cummax=pcummax,
            pos_cumdist=pcumdist.tolist(),
            pos_cutoff_index=pcutoffidx)

    return results

# performance plotting

def plot_perf_metrics(metrics, image_path=None, title=None, figsize=None,
                      predictors=None, perf_scores=None, cutoff_score=None):

    plot_attrs = [
        dict(title="Dist", xlabel="score", ylabel="density", grid=True,
             legend=[['upper center'], dict(ncol=2, frameon=False, prop={'size':10})]),
        dict(title="CumDist", xlabel="score", grid=True,
             legend=[['upper center'], dict(ncol=2, frameon=False, prop={'size':10})]),
        dict(title="Perf", ylim=(0, 100), grid=True),
        dict(title="ROC", xlabel="False Positive Rate", ylabel="True Positive Rate", grid=True)
    ]

    def init_plots(axes):
        for ax, attrs in zip(axes, plot_attrs):
            if "title" in attrs:
                ax.set_title(attrs["title"])
            if "xlim" in attrs:
                ax.set_xlim(attrs["xlim"])
            if "ylim" in attrs:
                ax.set_ylim(attrs["ylim"])
            if "xlabel" in attrs:
                ax.set_xlabel(attrs["xlabel"])
            if "ylabel" in attrs:
                ax.set_ylabel(attrs["ylabel"])
            if "grid" in attrs:
                ax.grid(attrs["grid"])
            if "legend" in attrs:
                ax.legend(*(attrs["legend"][0]), **(attrs["legend"][1]))

    def plot_predictor(pred, m, axes, perf_scores=None, cutoff_score=None):
    	if "rmin" not in metrics[pred]:
    		axes[0].set_ylabel(pred)
    		return
    	
        rmin, rmax = m["rmin"], m["rmax"]

        cutoffs = np.array(m["cutoffs"])
        num_cutoffs = len(cutoffs)
        
        xmin, xmax = cutoffs[0], cutoffs[-1]
        
        perf = pd.DataFrame(m["perf"], index=cutoffs)
        best_perf = m["best_perf"]
        
        perf_scores = perf_scores or best_perf.keys()
        cutoff_score = "MCC" if "MCC" in perf_scores else perf_scores[0]
        best_score = best_perf[cutoff_score]

        cutoff = m["best_perf_cutoff"][cutoff_score]
        cutoff_index = m["best_perf_index"][cutoff_score]
            
        nbins = np.array(m["neg_bins"])
        nwidths = nbins[1:] - nbins[0:-1]
        nbins = nbins[:-1]
        nhist = np.array(m["neg_hist"])
        nmax = float(nhist.max())
        ncumhist = np.cumsum(nhist)
        ncummax = float(ncumhist[-1])
        ncumdist = m["neg_cumdist"]
        ncutoffidx = m["neg_cutoff_index"]
        nweight = ncumdist[ncutoffidx]

        pbins = np.array(m["pos_bins"])
        pwidths = pbins[1:] - pbins[0:-1]
        pbins = pbins[:-1]
        phist = np.array(m["pos_hist"])
        pmax = float(phist.max())
        pcumhist = np.cumsum(phist)
        pcummax = float(pcumhist[-1])
        pcumdist = m["pos_cumdist"]
        pcutoffidx = m["pos_cutoff_index"]
        pweight = pcumdist[pcutoffidx]
        
        roc = pd.DataFrame(m["roc"])
        pred_auc = m["auc"]
        
        init_plots(axes)
        
        # distribution
        axes[0].set_ylabel(pred)
        axes[0].bar(nbins, nhist / nmax, color="b", lw=0, alpha=0.65, width=nwidths)
        axes[0].bar(pbins, phist / pmax, color="r", lw=0, alpha=0.65, width=pwidths)
        axes[0].legend(("NEG", "POS"), "upper left", ncol=1, frameon=False, prop={'size':10})
        axes[0].plot([cutoff, cutoff], [0.0, 1.0], "k--", alpha=0.5)

        # cumulative distribution
        axes[1].set_xlim(xmin, xmax)
        axes[1].plot(nbins, ncumdist, color="b", label="NEG")
        axes[1].plot(pbins, pcumdist, color="r", label="POS")
        axes[1].plot([xmin, xmax], [nweight, nweight], "k--", alpha=0.3)
        axes[1].plot([xmin, xmax], [pweight, pweight], "k--", alpha=0.3)
        axes[1].plot([cutoff, cutoff], [0.0, 1.0], "k--", alpha=0.5)
        axes[1].legend(("NEG", "POS"), "upper left", ncol=1, frameon=False, prop={"size":10})

        # performance
        score_color = {
            "MCC" : "r", "ACC" : "y",
            "PRECISION" : "b", "RECALL" : "c" }
            
        axes[2].set_xlim(xmin, xmax)
        labels = []
        for score_name in perf_scores:
            score_best_value = best_perf[score_name]
            if score_name in ["TP", "FN"]:
                factor = 100.0 / pcummax
            elif score_name in ["FP", "TN"]:
                factor = 100.0 / ncummax
            else:
	            factor = 100.0
            labels += ["{} = {:.2f}".format(score_name, score_best_value * factor)]
            color = score_color.get(score_name)
            #print("pred={} score={}, color={}".format(pred, score_name, color))
            if color is not None:
                axes[2].plot(cutoffs, perf[score_name] * factor, color=color)
            else:
                axes[2].plot(cutoffs, perf[score_name] * factor)
        axes[2].plot([cutoff, cutoff], [0.0, 100.0], "k--", alpha=0.5)
        axes[2].plot([xmin, xmax], [best_score, best_score], "k--", alpha=0.5)
        axes[2].set_xlabel("cutoff = {:.3f}".format(cutoff))
        axes[2].legend(tuple(labels), "upper left", ncol=1, frameon=False, prop={"size":10})
        #axes[2].legend(("MCC = {:.2f}".format(best_mcc), "ACC = {:.2f}".format(best_acc)), "upper left",
        #                 ncol=1, frameon=False, prop={"size":10})

        # ROC curve
        axes[3].plot(roc["FPR"], roc["TPR"])
        axes[3].plot([0, 1], [0, 1], 'k--')
        axes[3].legend(("AUC = {:.3f}".format(pred_auc), ), "lower right", frameon=False, prop={"size":10})
      
    title = title or metrics.get("title")

    predictors = predictors or metrics["predictors"]
    assert len(set(predictors) & set(metrics["predictors"])) == len(predictors)

    metrics = metrics["metrics"]

    if image_path is not None:
        plt.ioff()

    fig, axes = plt.subplots(nrows=len(predictors), ncols=4, figsize=figsize or (16,4 * len(predictors)))
    plt.subplots_adjust(wspace=0.2, hspace=0.35)

    if title is not None:
        fig.suptitle(title, fontsize=12)

    if len(predictors) == 1:
        pred = predictors[0]
        plot_predictor(pred, metrics[pred], axes, perf_scores, cutoff_score)
    else:
        for i, pred in enumerate(predictors):
        	plot_predictor(pred, metrics[pred], axes[i,:], perf_scores, cutoff_score)

    if image_path is not None:
        plt.savefig(image_path, bbox_inches='tight', pad_inches=0.2)
        plt.close(fig)
    else:
        plt.show()
