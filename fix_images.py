import sys

def fix_007(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    image_line_idx = -1
    image_line_content = ""
    for i, line in enumerate(lines):
        if "![Constructor Injection Action]" in line:
            image_line_idx = i
            image_line_content = line
            break

    if image_line_idx != -1:
        # Remove the line (and potentially surrounding empty lines if added by manage_images.py)
        # manage_images added \n\nTAG\n\n. So checking surrounding lines.
        del lines[image_line_idx]
        # Check for empty lines around
        if lines[image_line_idx].strip() == "":
             del lines[image_line_idx]
        if lines[image_line_idx-1].strip() == "":
             del lines[image_line_idx-1]

        # Find insertion point: Before the code block containing OrderService
        insert_idx = -1
        for i, line in enumerate(lines):
            if "public sealed class OrderService" in line:
                # Search backwards for ```csharp
                for j in range(i, -1, -1):
                    if lines[j].strip().startswith("```csharp"):
                        insert_idx = j
                        break
                break

        if insert_idx != -1:
            lines.insert(insert_idx, image_line_content + "\n")
            with open(filepath, 'w') as f:
                f.writelines(lines)
            print("Fixed 007")
        else:
            print("Could not find insertion point for 007")
    else:
        print("Image tag not found in 007")

def fix_013(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    image_line_idx = -1
    image_line_content = ""
    for i, line in enumerate(lines):
        if "![Exception Filter]" in line:
            image_line_idx = i
            image_line_content = line
            break

    if image_line_idx != -1:
        del lines[image_line_idx]
        if lines[image_line_idx].strip() == "":
             del lines[image_line_idx]
        if lines[image_line_idx-1].strip() == "":
             del lines[image_line_idx-1]

        # Find insertion point: After the code block containing PaymoPaymentGatewayAdapter
        insert_idx = -1
        in_adapter_block = False
        for i, line in enumerate(lines):
            if "public sealed class PaymoPaymentGatewayAdapter" in line:
                in_adapter_block = True

            if in_adapter_block and line.strip().startswith("```") and not line.strip().startswith("```csharp"):
                insert_idx = i + 1
                break

        if insert_idx != -1:
            lines.insert(insert_idx, "\n" + image_line_content)
            with open(filepath, 'w') as f:
                f.writelines(lines)
            print("Fixed 013")
        else:
            print("Could not find insertion point for 013")
    else:
        print("Image tag not found in 013")

if __name__ == "__main__":
    fix_007("docs/isa_hasa_cs_study_007.md")
    fix_013("docs/isa_hasa_cs_study_013.md")
