import olca_schema as schema

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple


@dataclass
class CalculationSetup:
    product_system: Optional[schema.Ref] = None
    process: Optional[schema.Ref] = None
    impact_method: Optional[schema.Ref] = None
    with_costs: Optional[bool] = None
    with_regionalization: Optional[bool] = None
    nw_set: Optional[schema.Ref] = None
    allocation_method: Optional[schema.AllocationType] = None
    parameter_redefs: Optional[List[schema.ParameterRedef]] = None
    amount: Optional[float] = None
    unit: Optional[schema.Ref] = None
    flow_property: Optional[schema.Ref] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {}
        if self.product_system is not None:
            d['productSystem'] = self.product_system.to_dict()
        if self.process is not None:
            d['process'] = self.process.to_dict()
        if self.impact_method is not None:
            d['impactMethod'] = self.impact_method.to_dict()
        if self.with_costs is not None:
            d['withCosts'] = self.with_costs
        if self.with_regionalization is not None:
            d['withRegionalization'] = self.with_regionalization
        if self.nw_set is not None:
            d['nwSet'] = self.nw_set.to_dict()
        if self.allocation_method is not None:
            d['allocationMethod'] = self.allocation_method.value
        if self.parameter_redefs is not None:
            d['parameterRedefs'] = []
            for e in self.parameter_redefs:
                d['parameterRedefs'].append(e.to_dict())
        if self.amount is not None:
            d['amount'] = self.amount
        if self.unit is not None:
            d['unit'] = self.unit.to_dict()
        if self.flow_property is not None:
            d['flowProperty'] = self.flow_property.to_dict()
        return d


@dataclass
class ProductResult:
    process: Optional[schema.Ref] = None
    product: Optional[schema.Ref] = None
    amount: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {}
        if self.process is not None:
            d['process'] = self.process.to_dict()
        if self.product is not None:
            d['product'] = self.product.to_dict()
        if self.amount is not None:
            d['amount'] = self.amount
        return d

    @staticmethod
    def from_dict(d: dict) -> 'ProductResult':
        result = ProductResult()
        if v := d.get('process'):
            result.process = v
        if v := d.get('product'):
            result.product = v
        if v := d.get('amount'):
            result.amount = v
        return result


@dataclass
class ContributionItem:
    item: Optional[schema.Ref] = None
    amount: Optional[float] = None
    share: Optional[float] = None
    rest: Optional[bool] = None
    unit: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        json: Dict[str, Any] = {}
        if self.item is not None:
            json['item'] = self.item.to_dict()
        if self.amount is not None:
            json['amount'] = self.amount
        if self.share is not None:
            json['share'] = self.share
        if self.rest is not None:
            json['rest'] = self.rest
        if self.unit is not None:
            json['unit'] = self.unit
        return json

    @staticmethod
    def from_dict(d: dict) -> 'ContributionItem':
        item = ContributionItem()
        if v := d.get('item'):
            item.item = schema.Ref.from_dict(v)
        if v := d.get('amount'):
            item.amount = v
        if v := d.get('share'):
            item.share = v
        if v := d.get('rest'):
            item.rest = v
        if v := d.get('unit'):
            item.unit = v
        return item


class ProcessProduct:

    def __init__(self, process: schema.Ref, flow: schema.Ref):
        self.process = process
        self.flow = flow

    @staticmethod
    def from_dict(d: dict):
        process = None
        if process_dict := d.get('process'):
            process = schema.Ref.from_dict(process_dict)
        flow = None
        if flow_dict := d.get('flow'):
            flow = schema.Ref.from_dict(flow_dict)
        return ProcessProduct(process, flow)


class UpstreamNode:

    def __init__(self, product: ProcessProduct, result=0.0):
        self.product = product
        self.result = result
        self.childs: List[UpstreamNode] = []

    @staticmethod
    def from_dict(d: dict) -> 'UpstreamNode':
        product = None
        if product_dict := d.get('product'):
            product = ProcessProduct.from_dict(product_dict)
        result = d.get('result', 0.0)
        node = UpstreamNode(product, result)
        childs: List[dict] = d.get('childs')
        if childs is not None:
            for child in childs:
                node.childs.append(UpstreamNode.from_dict(child))
        return node


class UpstreamTree:

    def __init__(self, ref: schema.Ref, root: UpstreamNode):
        self.ref = ref
        self.root = root

    @staticmethod
    def from_dict(json: dict) -> 'UpstreamTree':
        ref = None
        if ref_dict := json.get('ref'):
            ref = schema.Ref.from_dict(ref_dict)
        root = None
        if root_dict := json.get('root'):
            root = UpstreamNode.from_dict(root_dict)
        return UpstreamTree(ref, root)

    def traverse(self, fn: Callable[[Tuple[UpstreamNode, int]], None]):

        def traverse_(parent: UpstreamNode, depth: int):
            if not parent:
                return
            fn((parent, depth))
            if parent.childs:
                for child in parent.childs:
                    traverse_(child, depth + 1)

        traverse_(self.root, 0)
