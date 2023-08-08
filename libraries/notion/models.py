from enum import Enum


class NotionPagePropertyType(Enum):
    """
    Enum for the notion page property types.
    """

    SELECT = 1
    PEOPLE = 2
    RICH_TEXT = 3
    RELATION = 4
    LAST_EDITED_TIME = 5
    TITLE = 6
    OTHER = 7
    CREATED_TIME = 8
    CREATED_BY = 9
    DATE = 10
    FILES = 11
    MULTI_SELECT = 12


class NotionPageProperty:
    def __init__(self, name: str, property_dict: dict):
        self.name = name
        self.type_name = property_dict["type"]
        self.type = self._determine_property_type(self.type_name)
        self.content = property_dict[self.type_name]
        self.children = []

    @staticmethod
    def _determine_property_type(type_name: str) -> NotionPagePropertyType:
        """
        Determine the property type from the type name.

        :param type_name: The type name.
        :return: The property type.
        """
        if type_name.lower() == "select":
            return NotionPagePropertyType.SELECT
        elif type_name.lower() == "people":
            return NotionPagePropertyType.PEOPLE
        elif type_name.lower() == "rich_text":
            return NotionPagePropertyType.RICH_TEXT
        elif type_name.lower() == "relation":
            return NotionPagePropertyType.RELATION
        elif type_name.lower() == "last_edited_time":
            return NotionPagePropertyType.LAST_EDITED_TIME
        elif type_name.lower() == "title":
            return NotionPagePropertyType.TITLE
        elif type_name.lower() == "created_time":
            return NotionPagePropertyType.CREATED_TIME
        elif type_name.lower() == "created_by":
            return NotionPagePropertyType.CREATED_BY
        elif type_name.lower() == "date":
            return NotionPagePropertyType.DATE
        elif type_name.lower() == "files":
            return NotionPagePropertyType.FILES
        elif type_name.lower() == "multi_select":
            return NotionPagePropertyType.MULTI_SELECT

        else:
            return NotionPagePropertyType.OTHER

    def to_dict(self) -> dict:
        """
        Convert the notion page property to a dictionary.

        :return: The dictionary.
        """
        return {"type": self.type_name, self.type_name: self.content}


class NotionBlockType(Enum):
    """
    Enum for the notion block types.
    """

    PARAGRAPH = 1
    HEADING_3 = 2
    HEADING_2 = 3
    HEADING_1 = 4
    BULLETED_LIST_ITEM = 5
    CHILD_DATABASE = 6
    DIVIDER = 7
    OTHER = 8
    COLUMN_LIST = 9
    TABLE = 10
    TABLE_ROW = 11


class NotionBlock:
    def __init__(self, block_dict: dict):
        self.object: str = block_dict["object"]
        self.id: str = block_dict["id"]
        self.type_name: str = block_dict["type"]
        self.type: NotionBlockType = self._determine_block_type(self.type_name)
        self.content: dict = block_dict[self.type_name]
        self.has_children: bool = block_dict["has_children"]

    @staticmethod
    def _determine_block_type(type_name: str) -> NotionBlockType:
        """
        Determine the block type from the type name.

        :param type_name: The type name.
        :return: The block type.
        """
        type_name = type_name.lower()
        if type_name == "paragraph":
            return NotionBlockType.PARAGRAPH
        elif type_name == "heading_3":
            return NotionBlockType.HEADING_3
        elif type_name == "heading_2":
            return NotionBlockType.HEADING_2
        elif type_name == "heading_1":
            return NotionBlockType.HEADING_1
        elif type_name == "bulleted_list_item":
            return NotionBlockType.BULLETED_LIST_ITEM
        elif type_name == "child_database":
            return NotionBlockType.CHILD_DATABASE
        elif type_name == "divider":
            return NotionBlockType.DIVIDER
        elif type_name == "column_list":
            return NotionBlockType.COLUMN_LIST
        elif type_name == "table":
            return NotionBlockType.TABLE
        elif type_name == "table_row":
            return NotionBlockType.TABLE_ROW
        else:
            return NotionBlockType.OTHER

    def to_dict(self) -> dict:
        """
        Convert the notion block to a dictionary.

        :return: The dictionary.
        """
        return {
            "object": self.object,
            "type": self.type_name,
            self.type_name: self.content,
        }
