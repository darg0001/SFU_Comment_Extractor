########################
# Author: Kavan Shukla #
########################
import pandas as pd
import argparse

def get_arguments():
    '''
    argparse object initialization and reading input and output file paths.
    input files: new_comments_preprocessed (-i1), old_comments_preprocessed.csv (-i2),
                 comments_to_flag.txt (-i3)
    output file: final_merged_comments.csv (-o) 
    '''
    parser = argparse.ArgumentParser(description='csv file identifying duplicates between new and old comments')
    parser.add_argument('--new_comments_csv', '-i1', type=str, dest='new_comments_preprocessed', action='store',
                        #default='../../Sample_Resources/Sample_Comments_CSVs/new_comments_preprocessed.csv',
                        default=r'/Users/vkolhatk/Data/GnM_CSVs/intermediate_csvs/new_comments_preprocessed.csv',
                        help="the input csv file for new_comments generated from preprocessing script")

    parser.add_argument('--old_comments_csv', '-i2', type=str, dest='old_comments_preprocessed', action='store',
                        #default='../../Sample_Resources/Sample_Comments_CSVs/old_comments_preprocessed.csv',
                        default=r'/Users/vkolhatk/Data/GnM_CSVs/intermediate_csvs/old_comments_preprocessed_all_cols.csv',
                        help="the input csv file for old_comments generated from preprocessing script")

    parser.add_argument('--comments_to_flag', '-i3', type=str, dest='comments_to_flag', action='store',
                        #default='../../Sample_Resources/Sample_Comments_CSVs/comments_to_flag.txt',
                        default=r'/Users/vkolhatk/Data/GnM_CSVs/intermediate_csvs/comments_to_flag.txt',
                        help="the input txt file generated from duplicate_filter.py containing comment_counters to flag")

    parser.add_argument('--final_csv', '-o', type=str, dest='final_csv', action='store',
                        #default='../../Sample_Resources/Sample_Comments_CSVs/final_merged_comments.csv',
                        default=r'/Users/vkolhatk/Data/GnM_CSVs/intermediate_csvs/final_merged_comments.csv',
                        help="the output file containing both source1 and source2 comments")

    args = parser.parse_args()
    return args

def merge_sources(args):
    '''
     Given an argparse object, this module creates a dictionary of comment_counters present
     in comments_to_flag.txt as key and value as {'exact_match':[<comment_counters>],'similar':[<comment_counters>]}
     based on the weighted score and token sort score
     Concatenates the dataframes of csvs from both the sources (new and old comments)
     Adds a column 'flag' and populates it with the values of main_dict keys (where key is comment_counter)

    :param args: argparse object containing the input and output file paths as attributes

    '''
    flag_list = []
    
    with open(args.comments_to_flag,'r') as flag:
        for f in flag.readlines():
             flag_list.append(f.strip().split(','))

    main_dict = {k[0]:{v:[] for v in ['exact_match','similar']} for k in flag_list }

    for i in flag_list:
        weighted_ratio = int(i[-2])
        token_sort_ratio = int(i[-1])
        if main_dict.get(i[0]):
            if all(check_score in range(85, 97) for check_score in [weighted_ratio,token_sort_ratio]):
                main_dict[i[0]]['similar'].append(i[1])
            if all(check_score in range(97, 101) for check_score in [weighted_ratio,token_sort_ratio]):
                main_dict[i[0]]['exact_match'].append(i[1])
                
    new_comments = pd.read_csv(args.new_comments_preprocessed)
    old_comments = pd.read_csv(args.old_comments_preprocessed)
    old_comments.rename(columns = {'ID':'comment_id'}, inplace = True)
    # old_comments.rename(columns = {'timestamp':'post_time'}, inplace = True)
                
    merging_final = pd.concat([old_comments, new_comments])

    ''' 
    following line of commented code will delete the comments from the final csv 
    based on the comment_counters in comments_to_delete.txt
    '''
    # merging_final = merging_final.query('comment_counter not in @list_of_comments_to_delete')

    duplicate_flag_df = pd.DataFrame(list(main_dict.items()), columns=['comment_counter', 'duplicate_flag'])

    # Merging final csv with flagged dataframe
    final = pd.merge(merging_final,duplicate_flag_df,on='comment_counter',how='outer')

    # filling NaN values in duplicate_flag column with default value
    final['duplicate_flag'].fillna("""{'exact_match':[],'similar':[]}""", inplace=True)

    # renaming column names
    final.rename(columns = {'author':'comment_author'}, inplace = True)
    final.rename(columns = {'text_preprocessed':'comment_text'}, inplace = True)

    # reordering columns
    final = final[['article_id', 'comment_counter', 'comment_author', 'timestamp', 'post_time', 'comment_text', 
                    'duplicate_flag', 'TotalVotes', 'posVotes', 'negVotes', 'vote', 'reactions', 'replies',
                    'comment_id', 'parentID', 'threadID' , 'streamId', 'edited', 'isModerator', 'highlightGroups',
                    'moderatorEdit', 'descendantsCount', 'threadTimestamp', 'flagCount', 'sender_isSelf', 
                    'sender_loginProvider', 'data_type', 'is_empty', 'status']]
    
    return final

if __name__=="__main__":
    args = get_arguments()
    merged_comments = merge_sources(args)
    merged_comments.to_csv(args.final_csv, index=False)