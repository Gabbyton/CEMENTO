class WrongFileFormatError(Exception):
    def __init__(self, message="Wrong file format provided"):
        self.message = message
        super().__init__(self.message)

class DisconnectedTermError(Exception):
    def __init__(self, term_id, term_content):
        if not term_content.strip():
            self.message = f"Term with id {term_id} is not connected to any other term."
        else:
            self.message = f"Term with content: {term_content}, is not connected to any other term."
        super().__init__(self.message)

class DisconnectedEdgeError(Exception):
    def __init__(self, message):
        super().__init__(message)

class MissingParentEdgeError(DisconnectedEdgeError):
    def __init__(self, edge_id, edge_content):
        if not edge_content.strip():
            self.message = f"Edge with id {edge_id} does not have a source (parent) connected."
        else:
            self.message = f"Edge with content: {edge_content}, does not have a source (parent) connected."
        super().__init__(self.message)

class MissingChildEdgeError(DisconnectedEdgeError):
    def __init__(self, edge_id, edge_content):
        if not edge_content.strip():
            self.message = f"Edge with id {edge_id} does not have a target (child) connected."
        else:
            self.message = f"Edge with content: {edge_content}, does not have a target (child) connected."
        super().__init__(self.message)

class FloatingEdgeError(DisconnectedEdgeError):
    def __init__(self, edge_id, edge_content):
        if not edge_content:
            self.message = f"Edge with id {edge_id} does not have anything connected."
        else:
            self.message = f"Edge with content: {edge_content}, does not have anything connected."
        super().__init__(self.message)

class CircularEdgeError(DisconnectedEdgeError):
    def __init__(self, edge_id, edge_content):
        if not edge_content:
            self.message = f"Edge with id {edge_id} is only connected to itself. Please ignore."
        else:
            self.message = f"Edge with content: {edge_content}, is only connected to itself. Please ignore."
        super().__init__(self.message)

class BlankLabelError(Exception):
    def __init__(self, message):
        super().__init__(message)

class BlankTermLabelError(BlankLabelError):
    def __init__(self, term_id):
        self.message = f"Term with id {term_id} does not have a label."
        super().__init__(self.message)

class BlankEdgeLabelError(BlankLabelError):
    def __init__(self, edge_id, connected_terms):
        if not connected_terms:
            self.message = f"Edge with id {edge_id} does not have a label."
        else:
            self.message = f"Edge connected to {' and '.join(connected_terms)}, does not have a label."
        super().__init__(self.message)
