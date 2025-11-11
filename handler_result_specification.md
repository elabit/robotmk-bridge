# Oxygen handler result specification
```
{
  "$defs": {
    "RobotmkBridgeKeywordDict": {
      "properties": {
        "pass": {
          "title": "Pass",
          "type": "boolean"
        },
        "name": {
          "title": "Name",
          "type": "string"
        },
        "elapsed": {
          "title": "Elapsed",
          "type": "number"
        },
        "tags": {
          "items": {
            "type": "string"
          },
          "title": "Tags",
          "type": "array"
        },
        "messages": {
          "items": {
            "type": "string"
          },
          "title": "Messages",
          "type": "array"
        },
        "teardown": {
          "$ref": "#/$defs/RobotmkBridgeKeywordDict"
        },
        "keywords": {
          "items": {
            "$ref": "#/$defs/RobotmkBridgeKeywordDict"
          },
          "title": "Keywords",
          "type": "array"
        }
      },
      "required": [
        "pass",
        "name"
      ],
      "title": "RobotmkBridgeKeywordDict",
      "type": "object"
    },
    "RobotmkBridgeSuiteDict": {
      "properties": {
        "name": {
          "title": "Name",
          "type": "string"
        },
        "tags": {
          "items": {
            "type": "string"
          },
          "title": "Tags",
          "type": "array"
        },
        "setup": {
          "$ref": "#/$defs/RobotmkBridgeKeywordDict"
        },
        "teardown": {
          "$ref": "#/$defs/RobotmkBridgeKeywordDict"
        },
        "metadata": {
          "additionalProperties": {
            "type": "string"
          },
          "title": "Metadata",
          "type": "object"
        },
        "suites": {
          "items": {
            "$ref": "#/$defs/RobotmkBridgeSuiteDict"
          },
          "title": "Suites",
          "type": "array"
        },
        "tests": {
          "items": {
            "$ref": "#/$defs/RobotmkBridgeTestCaseDict"
          },
          "title": "Tests",
          "type": "array"
        }
      },
      "required": [
        "name"
      ],
      "title": "RobotmkBridgeSuiteDict",
      "type": "object"
    },
    "RobotmkBridgeTestCaseDict": {
      "properties": {
        "name": {
          "title": "Name",
          "type": "string"
        },
        "keywords": {
          "items": {
            "$ref": "#/$defs/RobotmkBridgeKeywordDict"
          },
          "title": "Keywords",
          "type": "array"
        },
        "tags": {
          "items": {
            "type": "string"
          },
          "title": "Tags",
          "type": "array"
        },
        "setup": {
          "$ref": "#/$defs/RobotmkBridgeKeywordDict"
        },
        "teardown": {
          "$ref": "#/$defs/RobotmkBridgeKeywordDict"
        }
      },
      "required": [
        "name",
        "keywords"
      ],
      "title": "RobotmkBridgeTestCaseDict",
      "type": "object"
    }
  },
  "$ref": "#/$defs/RobotmkBridgeSuiteDict"
}
```