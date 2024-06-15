from typing import Dict, Optional, Union
from justatom.tooling.stl import merge_in_order
from pathlib import Path
from loguru import logger
from yasearch.etc.pattern import singleton
from yasearch.modeling.mask import IBaseModel
from yasearch.modeling.prime import (
    IPFBERTModel,
    E5Model,
    E5LModel,
    E5SModel,
    ATOMICLModel,
    ATOMICModel,
    ATOMICSModel,
)
from yasearch.processing.mask import IProcessor
from yasearch.processing.prime import (
    M1LMProcessor,
    M2LMProcessor,
    TRIPLETProcessor,
    ATOMICProcessor,
    INFERProcessor,
)
from yasearch.configuring.prime import Config


@singleton
class IInjector:

    AVAILABLE_COMPONENT_TYPE = ("model", "processor")

    def inject(
        self, component_type: str, component_name, props: Optional[Dict] = None
    ) -> Union[IBaseModel, IProcessor]:
        # Update model_props via lazy way through config.yaml
        assert (
            component_type in self.AVAILABLE_COMPONENT_TYPE
        ), f"Unknown `component_type`={component_type}. You can pass one of {','.join(self.AVAILABLE_COMPONENT_TYPE)}"
        component = None
        if component_type == "model":
            model_props = merge_in_order(props, Config.model.props)
            if component_name.is_dir():
                component = IBaseModel.load(Path(component_name), **model_props)
            elif str(component_name).lower() in ("ipfbert", "ifpbert", "fipbert"):
                component = IPFBERTModel(**model_props)
            elif str(component_name).lower() in ("e5large"):
                component = E5LModel(**model_props)
            elif str(component_name).lower() in ("e5small"):
                component = E5SModel(**model_props)
            elif str(component_name).lower() in "e5":
                component = E5Model(**model_props)
            else:
                logger.error(f"Could not inject component model=[{component_name}]")
                component = None
        elif component_type == "processor":
            processor_props = merge_in_order(props, Config.processor.props)
            if component_name.is_dir():
                component = IProcessor.load(Path(component_name), **processor_props)
            elif str(component_name).upper() in ("M1"):
                component = M1Processor(**processor_props)
            elif str(component_name).upper() in ("M2"):
                component = M2Processor(**processor_props)
            elif str(component_name).upper() in ("ATOMIC"):
                component = ATOMICProcessor(**processor_props)
            else:
                logger.error(
                    f"Could not inject component [{component_name}] of type [processor]"
                )
                component = None
        return component


Injector = IInjector()


__all__ = ["Injector"]
