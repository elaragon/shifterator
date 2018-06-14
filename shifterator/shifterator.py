"""
shifterator.py

Author: Ryan J. Gallagher, Network Science Institute, Northeastern University
Last updated: June 13th, 2018

TODO:
- Define funcs to plot insets to shift graph
- Define advanced shift graph func / decide what goes in an advanced shift
- Add funcs to shift class that allow for easy updating of type2freq dicts
- Clean up class docstrings to fit standards of where things should be described
  (whether it's in init or under class, and listing what funcs are available)
"""

import os
import sys
import warnings
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter

# ------------------------------------------------------------------------------
# ---------------------------- GENERAL SHIFT CLASS -----------------------------
# ------------------------------------------------------------------------------
class shift:
    def __init__(self, system_1, system_2, reference_value=None,
                 filenames=False, type2score_1=None, type2score_2=None,
                 stop_lens=None, delimiter=','):
        """
        Shift object for calculating weighted scores of two systems of types,
        and the shift between them

        Parameters
        ----------
        system_1, system_2: dict or str
            if dict, then keys are types of a system and values are frequencies
            of those types. if str and filenames=False, then the types are
            assumed to be tokens separated by white space. If str and
            filenames=True, then types are assumed to be tokens and text is read
            in line by line from the designated file and split on white space
        reference_value: float, optional
            the reference score from which to calculate the deviation. If None,
            defaults to the weighted score of system_1
        filenames: bool, optional
            True if system_1 and system_2 are filenames of files with text to
            parse
        type2score_1, type2score_2: dict or str, optional
            if dict, types are keys and values are "scores" associated with each
            type (e.g., sentiment). If str, either the name of a score dict or
            file path to a score dict, where types and scores are given on each
            line, separated by commas. If None and other type2score is None,
            defaults to uniform scores across types. Otherwise defaults to the
            other type2score dict
        stop_lens: iterable of 2-tuples, optional
            denotes intervals that should be excluded when calculating shift
            scores
        """
        # Load type2freq dictionaries
        if isinstance(system_1, dict) and isinstance(system_2, dict):
            self.type2freq_1 = system_1
            self.type2freq_2 = system_2
        elif isinstance(ref, basestring) and isinstance(comp, basestring):
            if filenames is True:
                self.type2freq_1 = get_freqs_from_file(system_1)
                self.type2freq_2 = get_freqs_from_file(system_2)
            elif filename is False:
                self.type2freq_1 = dict(Counter(system_1.split()))
                self.type2freq_2 = dict(Counter(system_2.split()))
        else:
            warning = 'Shift object was not given text, a file to parse, or '+\
                      'frequency dictionaries. Check input.'
            warnings.warn(warning, Warning)
            self.type2freq_1 = dict()
            self.type2freq_2 = dict()
        # Load type2score dictionaries
        self.stop_lens = stop_lens
        if type_dict_1 is not None and type_dict_2 is not None:
            self.type2score_1 = get_score_dictionary(type2score_1, stop_lens,
                                                     delimiter)
            self.type2score_2 = get_score_dictionary(type2score_2, stop_lens,
                                                     delimiter)
        elif type_dict_1 is not None:
            self.type2score_1 = get_score_dictionary(type2score_1, stop_lens,
                                                     delimiter)
            self.type2score_2 = self.word2score_1
        elif type_dict_2 is not None:
            self.type2score_2 = get_score_dictionary(type2score_2, stop_lens,
                                                     delimiter)
            self.type2score_1 = self.word2score_2
        else:
            self.type2score_1 = {t : 1 for t in self.type2freq_1}
            self.type2score_2 = {t : 1 for t in self.type2freq_2}
        # Set reference value
        if reference_value is not None:
            self.reference_value = reference_value
        else:
            self.reference_value = self.get_weighted_score(self.type2freq_1,
                                                           self.type2score_1)

        # TODO: add functions that allow you to easily update the type2freq dicts


    def get_weighted_score(self, type2freq, type2score):
        """
        Calculate the average score of the system specified by the frequencies
        and scores of the types in that system

        Parameters
        ----------
        type2freq: dict
            keys are types and values are frequencies
        type2score: dict
            keys are types and values are scores

        Returns
        -------
        s_avg: float
            Average weighted score of system
        """
        # Check we have a vocabulary to work with
        types = set(type2freq.keys()).intersection(set(type2score.keys()))
        if len(types) == 0:
            warning = 'No types in the frequency dict appear in the score dict'
            warnings.warn(warning, Warning)
            return
        # Get weighted score and total frequency
        f_total = sum([freq for t,freq in type2freq.items() if t in types])
        s_weighted = sum([type2score[t]*freq for t,freq in type2freq.items()
                          if t in types])
        s_avg = s_weighted / f_total
        return s_avg

    def get_shift_scores(self, type2freq_1=None, type2score_1=None,
                         type2freq_2=None, type2score_2=None,
                         reference_value=None, normalize=True, details=False):
        """
        Calculates the type shift scores between two systems

        Parameters
        ----------
        type2freq: dict
            keys are types and values are frequencies. If None, defaults to the
            system_1 and system_2 type2freq dicts respectively
        type2score: dict
            keys are types and values are scores. If None, defaults to the
            system_1 and system_2 type2score dicts respectively
        reference_value: float
            the reference score from which to calculate the deviation. If None,
            defaults to the weighted score given by type2freq_1 and type2score_1
        normalize: bool
            if True normalizes shift scores so they sum to 1
        details: bool, if True returns each component of the shift score and
                 the final normalized shift score. If false, only returns the
                 normalized shift scores

        Returns
        -------
        type2p_diff: dict
            if details is True, returns dict where keys are types and values are
            the difference in relatively frequency, i.e. p_i,2 - p_i,1 for type i
        type2s_diff: dict,
            if details is True, returns dict where keys are types and values are
            the relative differences in score, i.e. s_i,2 - s_i,1 for type i
        type2s_ref_diff: dict
            if details is True, returns dict where keys are types and values are
            relative deviation from reference score, i.e. 0.5*(s_i,2+s_i,1)-s_ref
            for type i
        type2shift_score: dict
            words are keys and values are shift scores
        """
        # Check input of type2freq and type2score dicts
        if type2freq_1 is None or type2score_1 is None:
            type2freq_1 = self.type2freq_1
            type2score_1 = self.type2score_1
        if type2freq_2 is None or type2score_2 is None:
            type2freq_2 = self.type2freq_2
            type2score_2 = self.type2score_2
        # Enforce common score vocabulary
        if set(type2score_1.keys()).difference(type2score_2.keys()) != 0:
            warning = 'Score dictionaries do not have a common vocabulary. '\
                      +'Shift is not well-defined.'
            warnings.warn(warning, Warning)
            return
        # Get observed types that are also in score dicts
        types_1 = set(type2freq_1.keys()).intersection(set(type2score_1.keys()))
        types_2 = set(type2freq_2.keys()).intersection(set(type2score_2.keys()))
        types = types_1.union(types_2)
        # Check input of reference value
        if reference_value is None:
            reference_value = self.get_weighted_score(type2freq_1, type2score_1)
        # Get total frequencies, and average score of reference
        total_freq_1 = sum([freq for t,freq in type2freq_1.items() if t in types])
        total_freq_2 = sum([freq for t,freq in type2freq_2.items() if t in types])
        s_avg_ref = self.get_weighted_score(type2freq_ref, type2score_ref)
        # Get relative frequency of words in reference and comparison
        type2p_1 = {t:type2freq_1[t]/total_freq_1 if t in type2freq_1 else 0
                    for t in types}
        type2p_2 = {t:type2freq_2[t]/total_freq_2 if t in type2freq_2 else 0
                    for t in types}
        # Calculate relative diffs in freq
        type2p_diff = {t:type2p_2[t]-type2p_1[t] for t in types}
        # Calculate relative diffs in score and relative diff from ref
        type2s_diff = {}
        type2s_ref_diff = {}
        for t in types:
            type2s_diff[t] = type2score_2[t]-type2score_1[t]
            type2s_ref_diff[t] = 0.5*(type2score_2[t]+type2score_1[t])-s_avg_ref
        # Calculate total shift scores
        type2shift_score = {t : type2p_diff[t]*type2s_ref_diff[t]\
                                +0.5*type2s_diff[t]*(type2p_2[t]+type2p_1[t])
                                for t in types if t in types}
        # Normalize the total shift scores
        if normalize:
            total_diff = abs(sum(type2shift_score.values()))
            type2shift_score = {t : shift_score/total_diff for t,shift_score
                                in type2shift_score.items()}
        # Set results in shift object
        self.type2p_diff = type2p_diff
        self.type2s_diff = type2s_diff
        self.type2s_ref_diff = type2s_ref_diff
        self.type2shift_score = type2shift_score
        # Return shift scores
        if details:
            return type2p_diff,type2s_diff,type2s_ref_diff,type2shift_score
        else:
            return type2shift_score

    def get_shift_graph(self, top_n=50, bar_colors=('#ffff80','#3377ff'),
                        bar_type_space=0.5, width_scaling=1.4, insets=True,
                        advanced=False, xlabel=None, ylabel=None, title=None,
                        xlabel_fontsize=18, ylabel_fontsize=18,
                        title_fontsize=14, show_plot=True, tight=True):
        # TODO: can the later arguments be passed as args straight to plotting?
        """
        Plot the shift graph between two systems of types

        Parameters
        ----------
        top_n: int
            display the top_n types as sorted by their absolute contribution to
            the difference between systems
        bar_colors: 4-tuple
            colors to use for bars where first and second entries are the colors
            for types that have positive and negative relative score differences
            relatively
        bar_type_space: float
            space between the end of each bar and the corresponding label
        width_scaling: float
            parameter that controls the width of the x-axis. If types overlap
            with the y-axis then increase the scaling
        insets: bool
            whether to show insets showing the cumulative contribution to the
            shift by ranked words, and the relative sizes of each system
        advanced: bool
            whether to return an advanced shift figure
        show_plot: bool
            whether to show plot on finish
        tight: bool
            whether to call plt.tight_layout() on the plot

        Returns
        -------
        ax
            matplotlib ax of shift graph. Displays shift graph if show_plot=True
        """
        if not advanced:
            return self.get_shift_graph_simple(top_n, bar_colors, bar_type_space,
                                               width_scaling, insets, xlabel,
                                               ylabel, title, xlabel_fontsize,
                                               ylabel_fontsize, title_fontsize,
                                               show_plot, tight)
        else:
            return self.get_shift_graph_advanced(top_n, bar_colors,
                                                 bar_type_space, width_scaling,
                                                 insets, xlabel, ylabel, title,
                                                 xlabel_fontsize, ylabel_fontsize,
                                                 title_fontsize, show_plot, tight)

    def get_shift_graph_simple(self, top_n=50, bar_colors=('#ffff80','#3377ff'),
                               bar_type_space=0.5, width_scaling=1.4,
                               insets=True, xlabel=None, ylabel=None, title=None,
                               xlabel_fontsize=18, ylabel_fontsize=18,
                               title_fontsize=14, show_plot=True, tight=True):
        # TODO: can the later arguments be passed as args straight to plotting?
        """
        Plot the simple shift graph between two systems of types

        Parameters
        ----------
        top_n: int
            display the top_n types as sorted by their absolute contribution to
            the difference between systems
        bar_colors: 4-tuple
            colors to use for bars where first and second entries are the colors
            for types that have positive and negative relative score differences
            relatively
        bar_type_space: float
            space between the end of each bar and the corresponding label
        width_scaling: float
            parameter that controls the width of the x-axis. If types overlap
            with the y-axis then increase the scaling
        insets: bool
            whether to show insets showing the cumulative contribution to the
            shift by ranked words, and the relative sizes of each system
        show_plot: bool
            whether to show plot on finish
        tight: bool
            whether to call plt.tight_layout() on the plot

        Returns
        -------
        ax
            matplotlib ax of shift graph. Displays shift graph if show_plot=True
        """
        if self.type2shift_score is None:
            self.get_shift_scores(details=False)
        # Sort type scores and take top_n. Reverse for plotting
        type_scores = [(t, self.type2s_diff[t], self.type2p_diff[t],
                        self.type2shift_score[t]) for t in self.type2s_diff]
        # reverse?
        type_scores = sorted(type_scores, key=labmda x:abs(x[3]))[:top_n]
        type_diffs = [100*score for (t,s_diff,p_diff,score) in type_scores]
        # Get bar colors
        bar_colors = [bar_colors[0] if s_diff>0 else bar_colors[1]\
                      for (word,s_diff,p_diff,score) in word_scores]
        # Plot scores, height:width ratio = 2.5:1
        f,ax = plt.subplots(figsize=(6,15))
        ax.margins(y=0.01)
        # Plot the skeleton of the word shift
        # edgecolor thing is a workaround for a bug in matplotlib
        bars = ax.barh(range(1,len(type_scores)+1), word_diffs, .8, linewidth=1
                       align='center', color=bar_colors, edgecolor=['black']*top_n)
        # Add center dividing line
        ax.plot([0,0],[1,top_n], '-', color='black', linewidth=0.7)
        # Make sure there's the same amount of space on either side of y-axis,
        # and add space for word labels using 'width_scaling'
        # TODO: can we automate selection of width_scaling?
        x_min,x_max = ax.get_xlim()
        x_sym = width_scaling*max([abs(x_min),abs(x_max)])
        ax.set_xlim((-1*x_sym, x_sym))
        # Flip y-axis tick labels and make sure every 5th tick is labeled
        y_ticks = list(range(1,top_n,5))+[top_n]
        y_tick_labels = [str(n) for n in (list(range(top_n,1,-5))+['1'])]
        ax.set_yticks(y_ticks)
        ax.set_yticklabels(y_tick_labels)
        # Format word labels with up/down arrows and +/-
        type_labels = _get_shift_type_labels(type_scores)
        # Add word labels to bars
        ax = _set_bar_labels(bars, type_labels, bar_type_space=bar_type_space)
        # Set axis labels and title
        if xlabel is None:
            xlabel = 'Per type average score shift $\delta s_{avg,r}$ (%)'
        ax.set_xlabel(xlabel, fontsize=xlabel_fontsize)
        if ylabel is None:
            ylabel = 'Type rank $r$'
        ax.set_ylabel(ylabel, fontsize=ylabel_fontsize)
        if title is None:
            s_avg_1 = self.get_average_sentiment(self.type2freq_1,self.type2score_1)
            s_avg_2 = self.get_average_sentiment(self.type2freq_2,self.type2score_2)
            title = '$\Phi_{\Omega^{(2)}}$: $s_{avg}^{(ref)}=$'+'{0:.2f}'\
                    .format(s_avg_ref)+'\n'\
                    +'$\Phi_{\Omega^{(1)}}$: $s_{avg}^{(comp)}=$'+'{0:.2f}'\
                    .format(s_avg_comp)
        ax.set_title(title_str, fontsize=14)
        # Show and return plot
        if tight:
            plt.tight_layout()
        if show_plot:
            plt.show()
        return ax

    def get_shift_graph_advanced(self, top_n=50, bar_colors=('#ffff80','#3377ff'),
                                 bar_type_space=0.5, width_scaling=1.4,
                                 xlabel=None, ylabel=None, title=None,
                                 xlabel_fontsize=18, ylabel_fontsize=18,
                                 title_fontsize=14, show_plot=True, tight=True):
        """
        Plot the advanced shift graph between two systems of types

        Parameters
        ----------
        top_n: int
            display the top_n types as sorted by their absolute contribution to
            the difference between systems
        bar_colors: 4-tuple
            colors to use for bars where first and second entries are the colors
            for types that have positive and negative relative score differences
            relatively
        bar_type_space: float
            space between the end of each bar and the corresponding label
        width_scaling: float
            parameter that controls the width of the x-axis. If types overlap
            with the y-axis then increase the scaling
        insets: bool
            whether to show insets showing the cumulative contribution to the
            shift by ranked words, and the relative sizes of each system
        show_plot: bool
            whether to show plot on finish
        tight: bool
            whether to call plt.tight_layout() on the plot

        Returns
        -------
        ax
            matplotlib ax of shift graph. Displays shift graph if show_plot=True
        """
        # TODO: implement, can probably make a func that's shared between the
        # simple and detailed shift that creates the fundamental layout
        pass


# ------------------------------------------------------------------------------
# ------------------------------ HELPER FUNCTIONS ------------------------------
# ------------------------------------------------------------------------------
def get_score_dictionary(scores, stop_lens=None, delimiter=','):
    """
    Loads a dictionary of type scores

    Parameters
    ----------
    scores: dict or str
        if dict, then returns the dict automatically. If str, then it is either
        the name of a shifterator dictionary to load, or file path of dictionary
        to load. File should be two columns of types and scores on each line,
        separated by delimiter
            Options: 'labMT_english'
    stop_lens: iteratble of 2-tuples
        denotes intervals that should be excluded when calculating shift scores
    delimiter: str
        delimiter used in the dictionary file

    Returns
    -------
    type2score, dict
        dictionary where keys are types and values are scores of those types
    """
    if type(scores) is dict:
        return scores
    # Check if dictionary name is in shifterator data
    score_dicts = os.listdir('data')
    if scores in score_dicts:
        dict_file = 'data/'+scores
    elif  scores+'.csv' in score_dicts:
        dict_file = 'data/'+scores+'.csv'
    else: # Assume file path
        dict_file = scores
    # Load score dictionary
    type2score = {}
    with open(dict_file, 'r') as f:
        for line in f:
            t,score = line.strip().split(delimiter)
            type2score[t] = score
    # Filter dictionary of words inside stop lens
    if stop_lens is not None:
        for lower_stop,upper_stop in stop_lens:
            type2score = {t:score for t,score in type2score.items()
                          if score >= lower_stop and score <= upper_stop}
    return type2score

def get_freqs_from_file(filename):
    """
    Parses text of a file line by line, splitting across white space

    INPUT
    -----
    filename: str, file to load text from

    OUTPUT
    ------
    type2freq: dict, keys are words and values are frequencies of those words
    """
    type2freq = Counter()
    with open(filename, 'r') as f:
        for line in f:
            types = line.strip().split()
            type2freq.update(types)
    return dict(type2freq)

def _get_shift_type_labels(type_scores):
    """

    """
    type_labels = []
    for (t,s_diff,p_diff,total_diff) in type_scores:
        type_label = t
        if total_diff < 0:
            if p_diff < 0:
                type_label = u'\u2193'+type_label
            else:
                type_label = u'\u2191'+type_label
            if s_diff < 0:
                type_label = '-'+type_label
            else:
                type_label = '+'+type_label
        else:
            if s_diff < 0:
                type_label = type_label+'-'
            else:
                type_label = type_label+'+'
            if p_diff < 0:
                type_label = type_label+u'\u2193'
            else:
                type_label = type_label+u'\u2191'
        type_labels.append(type_label)
    return type_labels

def _set_bar_labels(bars, word_labels, bar_word_space=1.4):
    for bar_n,bar in enumerate(bars):
        y = bar.get_y()
        height = bar.get_height()
        width = bar.get_width()
        if word_diffs[bar_n] < 0:
            ha='right'
            space = -1*bar_word_space
        else:
            ha='left'
            space = bar_word_space
        ax.text(width+space, bar_n+1, word_labels[bar_n],
                ha=ha, va='center',fontsize=13)
    return ax