import os

import numpy
import tensorflow as tf
from typing import Any, List
from langchain.embeddings.base import Embeddings
from pydantic import BaseModel, Extra

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

class roBERTa_Embedding(Embeddings):
    
    embed: Any  #: :meta private:
    model_url: str = "https://tfhub.dev/jeongukjae/klue_roberta_cased_L-24_H-1024_A-16/1"
    """Model name to use."""
    
    def __init__(self, **kwargs: Any):
        
#        super().__init__(**kwargs)
        try:
            import tensorflow_hub as hub
        except ImportError:
            raise ImportError(
                "Could not import tensorflow-hub python package. "
                "Please install it with `pip install tensorflow-hub``."
            )
        try:
            import tensorflow_text  # noqa
        except ImportError:
            raise ImportError(
                "Could not import tensorflow_text python package. "
                "Please install it with `pip install tensorflow_text``."
            )
    
        self.preprocessor = hub.KerasLayer("https://tfhub.dev/jeongukjae/klue_roberta_cased_preprocess/1")
        self.encoder = hub.KerasLayer("https://tfhub.dev/jeongukjae/klue_roberta_cased_L-24_H-1024_A-16/1", trainable=True)
        
        text_input = tf.keras.layers.Input(shape=(), dtype=tf.string)
        encoder_inputs = self.preprocessor(text_input)
        encoder_outputs = self.encoder(encoder_inputs)
        pooled_output = encoder_outputs["pooled_output"]      # [batch_size, 1024].
        sequence_output = encoder_outputs["sequence_output"]  # [batch_size, seq_length, 1024].

        self.model = tf.keras.Model(text_input, pooled_output)

    class Config:
        """Configuration for this pydantic object."""

        extra = Extra.forbid

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Compute doc embeddings using a TensorflowHub embedding model.
        Args:
            texts: The list of texts to embed.
        Returns:
            List of embeddings, one for each text.
        """
        texts_to_tensor = [tf.constant([t]) for t in texts]
        embed_texts = [self.model(tensor) for tensor in texts_to_tensor]
        embeddings = [embed_t[0] for embed_t in embed_texts]
        return embeddings
        
    def embed_query(self, text: str) -> List[float]:
        """Compute query embeddings using a TensorflowHub embedding model.
        Args:
            text: The text to embed.
        Returns:
            Embeddings for the text.
        """
        text = tf.constant([text])
        embedding = self.model(text)[0]
        return embedding