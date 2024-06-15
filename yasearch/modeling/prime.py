from pathlib import Path
from tqdm.autonotebook import tqdm
import simplejson as json
from typing import Union, Optional, Dict, Any, List, Callable
from collections.abc import Iterator

import torch
from torch import Tensor
from transformers import AutoModel, AutoTokenizer
import numpy as np
import torch.nn as nn
from torch.functional import F

from yasearch.modeling.mask import ILanguageModel, IBaseModel, IDocEmbedder
from yasearch.modeling.div import IEmbedding, IAttention, MLAttention


class E5Model(ILanguageModel):
    """Base E5 family semantic model from hugging face"""

    pass


class E5SModel(ILanguageModel):
    """Small E5 family semantic model from huggingface"""

    pass


class E5LModel(ILanguageModel):
    """Large E5 family semantic model from huggingface"""

    pass


class ATOMICModel(ILanguageModel):
    """A Transformer Orchestration Model Involving Classification module. Base version for both inferene and high quality."""

    pass


class ATOMICSModel(ILanguageModel):
    """A Transformer Orchestration Model Involving Classification module. Small version optimized for fast inference."""

    pass


class ATOMICLModel(ILanguageModel):
    """A Transformer Orchestration Model Involving Classification module. Large version designed for the best quality."""

    pass


class IPFBERTModel(IBaseModel):
    """
    Positional Free Bidirectional Encoder Representation from Transformers
    """

    def __init__(
        self, embedding: nn.Module = None, attention: nn.Module = None, **props
    ):
        super(IPFBERTModel, self).__init__()
        if embedding is not None and attention is not None:
            self.embedding = embedding
            self.blocks = attention
        else:
            embedding_props = {k: props[k] for k in IEmbedding.props}
            self.embedding = IEmbedding(**embedding_props)

            if "num_blocks" in props:
                attention_props = {k: props[k] for k in MLAttention.props}
                self.blocks = MLAttention(**attention_props)
            else:
                attention_props = {k: props[k] for k in IAttention.props}
                self.blocks = IAttention(**attention_props)

    def generate_config(self):
        if isinstance(self.blocks, IAttention):
            num_blocks = -1
        else:
            num_blocks = self.blocks.config["num_blocks"]
        self.config = {"num_blocks": num_blocks}
        return self

    @classmethod
    def load(cls, pretrained_model_name_or_path):
        # Only need to load two components.
        with open(Path(pretrained_model_name_or_path) / "model_config.json") as fin:
            config = json.load(fin)
        # (1). Load the attention heads module.
        if config.get("num_blocks") > 0:
            att = MLAttention.load(pretrained_model_name_or_path)
        else:
            att = IAttention.load(pretrained_model_name_or_path)
        # (2). Load the embedding module.
        emb = IEmbedding.load(pretrained_model_name_or_path)

        return cls(embedding=emb, attention=att)

    def save(
        self, save_dir: Union[str, Path], state_dict: Optional[Dict[Any, Any]] = None
    ):
        """
        Save the model `state_dict` and its configuration file so that it can be loaded again.

        :param save_dir: The directory in which the model should be saved.
        :param state_dict: A dictionary containing the whole state of the module, including names of layers. By default, the unchanged state dictionary of the module is used.
        """
        Path(save_dir).mkdir(parents=True, exist_ok=True)
        # (1). Save the encoder with attention module and config(s)
        self.blocks.save(save_dir)
        # (2). Save the embedding module.
        self.embedding.save(save_dir)
        # (3). Generate and save the config
        self.generate_config().save_config(save_dir)

    def average_pool(
        self, last_hidden_states: torch.Tensor, attention_mask: torch.Tensor
    ) -> torch.Tensor:
        last_hidden = last_hidden_states.masked_fill(
            ~attention_mask[..., None].bool(), 0.0
        )

        return last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor = None,
        group_ids: torch.Tensor = None,
        norm: bool = True,
        average: bool = False,
    ):
        emb = self.embedding(input_ids)  # batch_size x max_seq_len x embedding_dim
        # attention_mask.shape == (batch_size, max_seq_len)
        out = self.blocks(input_tensor=emb, attention_mask=attention_mask)
        if average:
            out = self.average_pool(out, attention_mask=attention_mask)
        if norm:
            response = F.normalize(out, p=2, dim=len(out.shape) - 1)
        return response


class HFDocEmbedder(IDocEmbedder):
    """General class for HuggingFace embedder."""

    def __init__(
        self,
        model_name_or_path: str,
        pooling_mode: Callable[[Tensor, Tensor], Tensor] | str = "mean",
        prefix: str = "",
        device: str = "cpu",
    ):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
        self.model = AutoModel.from_pretrained(model_name_or_path)
        self.prefix = prefix
        self.device = device

    def encode(
        self,
        texts: List[str],
        batch_size: int = 256,
        max_length: int = 512,
        padding: bool = True,
        truncation: bool = True,
        normalize_embeddings: bool = True,
        device: str = None,
        verbose: bool = False,
        prefix: str = "",
        **kwargs,
    ) -> Iterator[np.ndarray]:
        device = device or self.device
        prefix = prefix or self.prefix

        self.model = self.model.to(device).eval()

        batch_gen = range(0, len(texts), batch_size)
        if verbose:
            batch_gen = tqdm(batch_gen)

        for batch_begin in batch_gen:
            batch_texts = texts[batch_begin : batch_begin + batch_size]
            batch_texts = [f"{prefix}{text}" for text in batch_texts]

            batch_inputs = self.tokenizer(
                batch_texts,
                max_length=max_length,
                padding=padding,
                truncation=truncation,
                return_tensors="pt",
                **kwargs,
            )

            batch_inputs = {k: vals.to(device) for k, vals in batch_inputs.items()}

            with torch.no_grad():
                outputs = self.model(**batch_inputs)

            outputs = outputs.last_hidden_state.cpu()

            embeddings = self._pooling_mode_func(
                outputs, batch_inputs["attention_mask"]
            )

            if normalize_embeddings:
                embeddings = F.normalize(embeddings, p=2, dim=1)

            yield embeddings.numpy()


class IRECModel(IBaseModel):
    """
    RECurrent based model processing tokens sequentially one by one.
    """

    def __init__(self):
        super(IRECModel, self).__init__()

    @classmethod
    def load(cls, pretrained_model_name_or_path):
        pass


__all__ = ["IPFBERTModel", "E5SModel", "E5Model", "HFDocEmbedder", "E5LModel"]
