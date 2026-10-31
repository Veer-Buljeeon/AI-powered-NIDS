"""Phase 2 - LSTM training.

Architecture per the project brief:
  LSTM(128, return_sequences=True) -> Dropout(0.3) -> LSTM(64) -> Dropout(0.3)
  -> Dense(num_classes, softmax)
Adam optimiser, categorical crossentropy, EarlyStopping(val_loss, patience=5),
up to 50 epochs. Input reshaped to (samples, 1, num_features). Trained on the
SMOTE-balanced training set, evaluated on the held-out test set, saved in
TensorFlow SavedModel format to core/models/lstm_model/.

batch_size=1024 and validation_split=0.1 are chosen here (not specified by the
brief): the batch size keeps 3M-row CPU training tractable, and the split gives
EarlyStopping a val_loss to monitor. The training arrays are shuffled before the
split so the validation fold is not a single-class block.
"""

from __future__ import annotations

import os

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")  # quieten TF info/warning spam

import time

import numpy as np

from _common import MODELS_DIR, evaluate, load_data, load_label_names

RANDOM_STATE = 42
BATCH_SIZE = 1024
MAX_EPOCHS = 50
VALIDATION_SPLIT = 0.1


def main():
    import tensorflow as tf
    from tensorflow.keras.callbacks import EarlyStopping
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.utils import to_categorical

    np.random.seed(RANDOM_STATE)
    tf.random.set_seed(RANDOM_STATE)

    X_train, y_train, X_test, y_test = load_data()
    label_names = load_label_names()
    num_classes = len(label_names)
    num_features = X_train.shape[1]
    print(f"[lstm] train={X_train.shape} test={X_test.shape} classes={num_classes}")

    # Reshape to (samples, timesteps=1, features); one-hot encode the labels.
    X_train_r = X_train.reshape((-1, 1, num_features)).astype("float32")
    X_test_r = X_test.reshape((-1, 1, num_features)).astype("float32")
    y_train_oh = to_categorical(y_train, num_classes=num_classes)

    # Shuffle before fit so validation_split (last 10%) is not a single-class block.
    perm = np.random.permutation(X_train_r.shape[0])
    X_train_r = X_train_r[perm]
    y_train_oh = y_train_oh[perm]

    model = Sequential([
        LSTM(128, return_sequences=True, input_shape=(1, num_features)),
        Dropout(0.3),
        LSTM(64),
        Dropout(0.3),
        Dense(num_classes, activation="softmax"),
    ])
    model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])
    model.summary()

    early_stop = EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True)
    t0 = time.time()
    model.fit(
        X_train_r, y_train_oh,
        validation_split=VALIDATION_SPLIT,
        epochs=MAX_EPOCHS, batch_size=BATCH_SIZE,
        callbacks=[early_stop], verbose=2,
    )
    print(f"[lstm] training took {(time.time() - t0) / 60:.1f} min")

    y_proba = model.predict(X_test_r, batch_size=BATCH_SIZE, verbose=0)
    y_pred = np.argmax(y_proba, axis=1)
    evaluate("lstm", y_test, y_pred, y_proba, label_names)

    out = MODELS_DIR / "lstm_model"
    model.save(str(out))  # SavedModel directory (Keras 2)
    print(f"[lstm] saved model to {out}")


if __name__ == "__main__":
    main()
