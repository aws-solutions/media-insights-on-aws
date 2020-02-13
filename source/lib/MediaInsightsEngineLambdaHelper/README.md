# Media Insights Engine Lambda Helper

This package serves as a helper library for developing the lambda functions that compose an operator
in the Media Insights Engine application.

Classes are provided for 4 common needs:

* Valid Status Syntax
* Output formatting
* Dataplane Interaction (Media / Metadata Persistence)
* Custom Errors


# Usage

Use the python `import` command. For example:

```
from MediaInsightsEngineLambdaHelper import OutputHelper
from MediaInsightsEngineLambdaHelper import MasExecutionError
from MediaInsightsEngineLambdaHelper import DataPlane
```
