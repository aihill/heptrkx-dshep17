import numpy as np
import matplotlib.pyplot as plt
import random
import os

def choosegpu(root='gpu'):

    stdout = os.popen('nvidia-smi').read().split('\n')
    
    device=0
    status = []
    for std in stdout:
        spl = std.split()
        if len(spl)==15:
            mem = spl[8]
            percent = spl[12]
            status.append( { "device": "gpu%d"%device,
                             "mem":mem,
                             "percent":percent}
            )
            
            device+=1

    ## pick the GOU with the less memory allocated
    status.sort( key = lambda v:v["mem"])

    print status
    gpu=status[0]["device"]
    flags = os.environ.get('THEANO_FLAGS')
    ## the theano flags are not really necessary, everything can be driven with CUDA_VISIBLE_DEVICES
    #add_theano = 'device=%s'%gpu.replace('gpu',root)
    #os.environ['THEANO_FLAGS']= flags+','+add_theano if flags else add_theano
    add_theano = 'device=gpu'.replace('gpu',root)
    os.environ['THEANO_FLAGS']= flags+','+add_theano if flags else add_theano
    os.environ['CUDA_VISIBLE_DEVICES']=gpu.replace('gpu','')
    print gpu

        

def score_function(y_true, y_pred):
    '''Compute a clustering score.
        
    Cluster ids should be nonnegative integers. A negative integer
    will mean that the corresponding point does not belong to any
    cluster.

    We first identify assigned clusters by taking the max count of 
    unique assigned ids for each true cluster. We remove all unassigned
    clusters (all assigned ids are -1) and all duplicates (the same
    assigned id has majority in several true clusters) except the one
    with the largest count. We add the counts, then divide by the number
    of events. The score should be between 0 and 1. 

    Parameters
    ----------
    y_true : np.array, shape = (n, 2)
        The ground truth.
        first column: event_id
        second column: cluster_id
    y_pred : np.array, shape = (n, 2)
        The predicted cluster assignment.
        first column: event_id
        second column: predicted cluster_id
    """
    '''
    score = 0.
    event_ids = y_true[:, 0]
    y_true_cluster_ids = y_true[:, 1]
    y_pred_cluster_ids = y_pred
    
    unique_event_ids = np.unique(event_ids)
    for event_id in unique_event_ids:
        event_indices = (event_ids==event_id)
        cluster_ids_true = y_true_cluster_ids[event_indices]
        cluster_ids_pred = y_pred_cluster_ids[event_indices]
        
        unique_cluster_ids = np.unique(cluster_ids_true)
        n_cluster = len(unique_cluster_ids)
        n_sample = len(cluster_ids_true)
        
        # assigned_clusters[i] will be the predicted cluster id
        # we assign (by majority) to true cluster i
        assigned_clusters = np.empty(n_cluster, dtype='int64')
        # true_positives[i] will be the number of points in
        # predicted cluster[assigned_clusters[i]]
        true_positives = np.full(n_cluster, fill_value=0, dtype='int64')
        for i, cluster_id in enumerate(unique_cluster_ids):
            # true points belonging to a cluster
            true_points = cluster_ids_true[cluster_ids_true == cluster_id]
            # predicted points belonging to a cluster
            found_points = cluster_ids_pred[cluster_ids_true == cluster_id]
            # nonnegative cluster_ids (negative ones are unassigned)
            assigned_points = found_points[found_points >= 0]
            # the unique nonnegative predicted cluster ids on true_cluster[i]
            n_sub_cluster = len(np.unique(assigned_points))
            # We find the largest predicted cluster in the true cluster.
            if(n_sub_cluster > 0):
                # sizes of predicted assigned cluster in true cluster[i]
                predicted_cluster_sizes = np.bincount(
                    assigned_points.astype(dtype='int64'))
                # If there are ties, we assign the tre cluster to the predicted
                # cluster with the smallest id (combined behavior of np.unique
                # which sorts the ids and np.argmax which returns the first
                # occurence of a tie).
                assigned_clusters[i] = np.argmax(predicted_cluster_sizes)
                true_positives[i] = len(
                    found_points[found_points == assigned_clusters[i]])
                # If none of the assigned ids are positive, the cluster is unassigned
                # and true_positive = 0
            else:
                assigned_clusters[i] = -1
                true_positives[i] = 0
                
        # resolve duplicates and count good assignments
        sorted = np.argsort(true_positives)
        true_positives_sorted = true_positives[sorted]
        assigned_clusters_sorted = assigned_clusters[sorted]
        good_clusters = assigned_clusters_sorted >= 0
        for i in range(len(assigned_clusters_sorted) - 1):
            assigned_cluster = assigned_clusters_sorted[i]
            # duplicates: only keep the last count (which is the largest
            # because of sorting)
            if assigned_cluster in assigned_clusters_sorted[i+1:]:
                good_clusters[i] = False
        n_good = np.sum(true_positives_sorted[good_clusters])
        score += 1. * n_good / n_sample
    score /= len(unique_event_ids)
    return score
                    
def display( pixelx, pixely, tracks):
    plt.figure( figsize=(10,10))
    plt.subplot(aspect='equal')
    for layer,r in enumerate([39,85,155,213,271,405,562,762,1000]):
        plt.gcf().gca().add_artist( plt.Circle((0, 0), r,color='b',  fill=False ,linestyle='--') )
    for itrack in np.unique(tracks):
        if itrack >= 0:
            hits_track = (tracks == itrack)
            plt.plot(pixelx[hits_track],pixely[hits_track],
                     marker='o', linestyle='none',
                     label='track %d'%itrack)
    itrack = -1
    hits_track = (tracks == itrack)
    plt.plot(pixelx[hits_track],pixely[hits_track],color='black', marker='o', fillstyle='none', linestyle='none', label='not associated')
    plt.xlim((-1100,1100))
    plt.ylim((-1100,1100))
    plt.legend(loc=(1.1,0.2))
    plt.show()
    
