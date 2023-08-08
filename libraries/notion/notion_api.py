from contextlib import suppress
from copy import deepcopy
from typing import List

import requests

from libraries.common import retry_on_bad_response
from libraries.sso_core.exceptions import (
    BadPayloadException,
    BadRequestException,
    ExceededRateLimitException,
    ServerSideException,
    UnauthorizedException,
)

from .models import NotionBlock, NotionBlockType, NotionPageProperty


class NotionAPI:
    def __init__(self, notion_credentials: dict):
        """
        Constructs NotionAPI object

        :param notion_credentials: dict containing credentials for Notion API
        """
        self.default_headers = self._set_headers(notion_credentials["INTERNAL_INTEGRATION_TOKEN"])

    @staticmethod
    def _set_headers(internal_integration_token: str) -> dict:
        """
        Sets headers for requests

        :param internal_integration_token: str containing internal integration token
        :return: dict containing headers
        """
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
            "Authorization": f"Bearer {internal_integration_token}",
        }

    def _get_headers(self, is_json=True, add_headers: dict = None) -> dict:
        """
        Gets headers for requests

        :param is_json: bool indicating whether to return json headers
        :param add_headers: dict containing additional headers
        :return: dict containing headers
        """
        headers = self.default_headers.copy()
        if is_json:
            headers["content-type"] = "application/json; charset=UTF-8"
        if add_headers:
            for key, value in add_headers.items():
                headers[key] = value
        return headers

    @staticmethod
    def _check_response(response: requests.Response) -> None:
        """
        Checks response for errors

        :param response: requests.Response object
        :return: None
        """
        if response.status_code == 429:
            raise ExceededRateLimitException(f"Notion API exceeded rate limit: {response.text}", response.status_code)
        elif response.status_code == 400:
            raise BadPayloadException(
                f"Notion API determined bad payload. Possibly exceeded size limit: {response.text}",
                response.status_code,
            )
        elif response.status_code in [401, 403]:
            raise UnauthorizedException(f"Notion API sent unauthorized: {response.text}", response.status_code)
        elif response.status_code >= 500:
            raise ServerSideException(f"Notion API server error: {response.text}", response.status_code)
        elif response.status_code != 200:
            raise BadRequestException(f"Notion API returned error: {response.text}", response.status_code)

    @retry_on_bad_response
    def _get_page(self, page_id: str) -> dict:
        """
        Get Notion page object

        :param page_id: str containing page id
        :return: dict containing page object
        """
        url = f"https://api.notion.com/v1/pages/{page_id}"

        response = requests.request("GET", url, headers=self._get_headers(is_json=False))
        self._check_response(response)

        return response.json()

    @retry_on_bad_response
    def _list_all_users(self) -> List[dict]:
        """
        Lists all users in Notion

        :return: list containing dicts of users
        """
        url = "https://api.notion.com/v1/users?page_size=100"

        response = requests.request("GET", url, headers=self._get_headers(is_json=False))
        self._check_response(response)

        return response.json()["results"]

    @retry_on_bad_response
    def _update_page(self, page_id: str, properties: List[NotionPageProperty]) -> None:
        """
        Updates page in Notion

        :param page_id: str containing page id
        :param properties: list containing dicts of properties to update
        :return: None
        """

        properties_dict = {page_property.name: page_property.to_dict() for page_property in properties}

        payload = {
            "properties": properties_dict,
        }

        url = f"https://api.notion.com/v1/pages/{page_id}"

        response = requests.request("PATCH", url, json=payload, headers=self._get_headers())
        self._check_response(response)

    @retry_on_bad_response
    def _get_block_children(self, parent_id: str) -> List[dict]:
        """
        Gets block children of parent

        :param parent_id: str containing parent id
        :return: list containing dicts of children
        """
        url = f"https://api.notion.com/v1/blocks/{parent_id}/children?page_size=100"

        response = requests.request("GET", url, headers=self._get_headers(is_json=False))
        self._check_response(response)

        return response.json()["results"]

    def _get_all_children(self, parent_id: str) -> List[NotionBlock]:
        """
        Gets all children of parent, including nested children

        Args:
            parent_id: id of parent block

        Returns: a list of NotionBlock
        """
        children = [NotionBlock(child) for child in self._get_block_children(parent_id)]
        for child in children:
            if child.has_children:
                child.content["children"] = self._get_all_children(child.id)
        return children

    @retry_on_bad_response
    def _update_block(self, block_id: str, block: NotionBlock) -> None:
        """
        Updates block in Notion

        :param block_id: str containing block id
        :param block: NotionBlock object
        :return: None
        """
        payload = self._convert_block_to_json(block)

        url = f"https://api.notion.com/v1/blocks/{block_id}"

        response = requests.request("PATCH", url, json=payload, headers=self._get_headers())
        self._check_response(response)

    def _convert_block_to_json(self, block: NotionBlock) -> dict:
        """
        Converts block to json

        :param block: NotionBlock object
        :return: dict containing block json
        """
        if block.content.get("children"):
            children = []
            for key in ["children", "cells"]:
                with suppress(KeyError):
                    for child in block.content[key]:
                        if isinstance(child, NotionBlock):
                            child = self._convert_block_to_json(child)
                        children.append(child)
                    block.content[key] = children
        block = block.to_dict()
        return block

    @retry_on_bad_response
    def _create_new_page_under_database(
        self,
        parent_id: str,
        children: List[NotionBlock],
        properties: List[NotionPageProperty],
    ) -> (str, str):
        """
        Create new page in Notion

        :param parent_id: str containing parent id of new page
        :param children: dict containing children of new page
        :param properties: dict containing properties of new page
        :return: str containing id of new page, str containing new page's url
        """
        properties_dict = {page_property.name: page_property.to_dict() for page_property in properties}

        children_list = [self._convert_block_to_json(child) for child in children]

        payload = {
            "parent": {
                "type": "database_id",
                "database_id": parent_id,
            },
            "properties": properties_dict,
            "children": children_list,
        }
        url = "https://api.notion.com/v1/pages"

        response = requests.request("POST", url, json=payload, headers=self._get_headers())
        self._check_response(response)

        response_dict = response.json()

        return response_dict["id"], response_dict["url"]

    @retry_on_bad_response
    def _append_children_to_object(self, parent_id: str, children: List[NotionBlock]) -> None:
        """
        Append a child element to the parent

        :param parent_id: str containing parent id
        :param children: list of NotionBlock containing child element
        :return: None
        """
        payload = {"children": [child.to_dict() for child in children]}

        url = f"https://api.notion.com/v1/blocks/{parent_id}/children"

        response = requests.request("PATCH", url, headers=self._get_headers(), json=payload)
        self._check_response(response)

    def _get_correct_user(self, user: str) -> dict:
        """
        Gets correct user from Notion

        :param user: str containing user's name
        :return: dict containing user object
        """
        users_json = self._list_all_users()
        names = user.split(" ")
        for json_user in users_json:
            is_user = True
            for name in names:
                if name.lower() not in json_user["name"].lower():
                    is_user = False

            if is_user:
                return json_user

    def _get_new_account_template_attributes(self) -> (List[NotionPageProperty], List[NotionBlock]):
        """
        Get attributes (properties and block children) of new account template

        :return: Two lists containing NotionPageProperty and NotionBlock (properties, children)
        """
        page_properties: dict = self._get_page(self.new_account_template)["properties"]
        page_children: List[dict] = self._get_block_children(self.new_account_template)

        properties: List[NotionPageProperty] = [
            NotionPageProperty(key, value) for key, value in page_properties.items()
        ]

        children: List[NotionBlock] = [NotionBlock(child) for child in page_children]
        return properties, children

    @retry_on_bad_response
    def _query_database_by_title(self, database_id: str, query_term: str) -> List[dict]:
        """
        Query database using a search term and the titles of each item

        :param database_id: str containing database id
        :param query_term: str containing query term
        :return: list containing dictionary representations of each resulting item
        """
        payload = {
            "page_size": 100,
            "filter": {"or": [{"property": "title", "text": {"contains": query_term}}]},
        }

        url = f"https://api.notion.com/v1/databases/{database_id}/query"

        response = requests.request("POST", url, json=payload, headers=self._get_headers())
        self._check_response(response)

        return response.json()["results"]

    def _set_bulleted_list_item_link(
        self, text_to_match: str, page_id: str, url: str, replace_only_matched_text: bool = False
    ) -> None:
        """
        Set the link of a bulleted list item

        :param text_to_match: str containing text to match
        :param page_id: str containing page id
        :param url: str containing url
        :param replace_only_matched_text: bool indicating if only the matched text should be replaced. If False, the
        bullet point text will be replaced with the linked text. If True, all text will remain, but the matched text
        only will be linked.
        :return: None
        """
        page_children = [NotionBlock(child) for child in self._get_block_children(page_id)]
        bullet_list_blocks = [child for child in page_children if child.type == NotionBlockType.BULLETED_LIST_ITEM]
        with suppress(StopIteration):
            for block in bullet_list_blocks:
                for item in block.content["text"]:
                    if item.get("plain_text") == text_to_match:
                        new_block = deepcopy(block)
                        item["text"]["link"] = {"url": url}
                        if not replace_only_matched_text:
                            new_block.content["text"] = [item]
                        self._update_block(new_block.id, new_block)
                        raise StopIteration
            raise ValueError(f"Could not find {text_to_match} in bullet list")

    def _get_database_pages(self, database_id: None):
        pages = {}

        has_next = True
        cursor = None
        while has_next:
            payload = {
                "page_size": 100,  # adjust the page size as per your needs
            }

            if cursor:
                payload["start_cursor"] = cursor

            response = requests.post(
                f"https://api.notion.com/v1/databases/{database_id}/query", headers=self._get_headers(), json=payload
            )

            response_data = response.json()
            results = response_data["results"]

            # Iterate through the response and extract the content and child content
            for item in results:
                if item["object"] != "page":
                    continue

                # Extract content
                try:
                    title = item["properties"]["\ufeffName"]["title"][0]["text"]["content"]
                except KeyError:
                    title = item["properties"]["Name"]["title"][0]["text"]["content"]
                item["title"] = title
                id = item["id"]
                pages[id] = item

            # Check if there are more pages available
            if has_next := response_data.get("has_more"):
                cursor = response_data["next_cursor"]

        return pages

    def get_page_content(self, page_id: str):
        endpoint = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100"

        response = requests.get(endpoint, headers=self._get_headers())
        data = response.json()

        page_content = []
        for block in data["results"]:
            if block["type"] == "paragraph":
                paragraph = "".join([t["plain_text"] for t in block["paragraph"]["rich_text"]])
                page_content.append(paragraph)

        return page_content
