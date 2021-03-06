import os
from tqdm import tqdm
import pickle
import pandas as pd
import numpy as np

from librosa import power_to_db
from librosa.core import load as load_wav
from librosa.effects import split
from librosa.feature import melspectrogram


def extract_log_mel_feats(set_type, path_to_csv, path_to_files, out_path, sr, fft_size, hop, n_mels):
    """
    Extract features from given files and store them in binary format.

    :param set_type:
    :param path_to_csv: path to loaded csv
    :param path_to_files: path to loaded data
    :param out_path: path to store extracted features
    :param sr: input files sample rate
    :param fft_size: size of fft window
    :param hop: hop size
    :param n_mels: number of mel band

    :return:

    """
    set_type = set_type.lower()
    if set_type not in ['train', 'test']:
        raise Exception('Such set type not supported: {}'.format(set_type))

    feats = []

    if set_type == 'train':
        meta = pd.read_csv(path_to_csv, sep='\t', header=None)
        meta.columns = ['file', 'unk1', 'unk2', 'duration', 'type']

        file_names = list(meta['file'])
        n_files = len(file_names)
        labels = list(meta['type'])

        uniq_labels = np.sort(np.unique(labels))
        label_to_id = {label: i for i, label in enumerate(uniq_labels)}

        print('Total files:', n_files)

        for i, (file_name, label) in tqdm(enumerate(zip(file_names, labels))):
            wav_data, sr = load_wav(os.path.join(path_to_files, file_name), sr=sr)
            for part in split(wav_data, top_db=30):
                start, end = part
                # skip ultra short parts
                if (end - start) < fft_size:
                    continue
                wav_part = wav_data[start:end]                
                mel_spec = melspectrogram(wav_part, n_fft=fft_size, hop_length=hop, n_mels=n_mels, fmax=sr // 2)
                log_mel_spec = power_to_db(mel_spec, ref=np.max)
                feats.append({
                    'fname': file_name,
                    'feature': log_mel_spec,
                    'label_id': label_to_id[label]
                })
        pickle.dump(feats, open(out_path, 'wb'))    
        return label_to_id
    else:
        for i, file_name in tqdm(enumerate(os.listdir(path_to_files))):
            wav_data, sr = load_wav(os.path.join(path_to_files, file_name), sr=sr)
            if len(wav_data) == 0:
                # print('Empty file:', file_name)
                wav_data = np.zeros(sr)
            mel_spec = melspectrogram(wav_data, n_fft=fft_size, n_mels=n_mels, fmax=sr // 2)
            log_mel_spec = power_to_db(mel_spec, ref=np.max)
            feats.append({
                'fname': file_name,
                'feature': log_mel_spec,
            })

    pickle.dump(feats, open(out_path, 'wb'))
