#ifndef HOLOSCAN_OPERATORS_OPENXR_UX_UX_WINDOW_RENDERER_HPP
#define HOLOSCAN_OPERATORS_OPENXR_UX_UX_WINDOW_RENDERER_HPP

#include <array>
#include <vector>

#include "ux_widgets.hpp"

namespace holoscan::openxr {
class UxWindowRenderer {
 public:
  void render(UxWindow& box);

 private:
  void drawAxes(float length);
};
}  // namespace holoscan::openxr

#endif  // HOLOSCAN_OPERATORS_OPENXR_UX_UX_WINDOW_RENDERER_HPP
