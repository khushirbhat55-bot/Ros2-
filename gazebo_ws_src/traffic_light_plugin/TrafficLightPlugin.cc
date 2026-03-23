#include <gz/sim/System.hh>
#include <gz/sim/components/Name.hh>
#include <gz/sim/components/Model.hh>
#include <gz/sim/components/Pose.hh>
#include <gz/plugin/Register.hh>
#include <gz/math/Pose3.hh>
#include <chrono>
#include <string>
#include <iostream>

using namespace gz;
using namespace sim;

class TrafficLightPlugin :
  public System,
  public ISystemPostUpdate
{
  private: double redDuration    = 5.0;
  private: double greenDuration  = 5.0;
  private: double yellowDuration = 2.0;

  private: enum Phase { RED, GREEN, YELLOW } currentPhase = RED;
  private: double phaseStartTime = -1.0;
  private: bool   initialized    = false;

  private: Entity redEntity    = kNullEntity;
  private: Entity yellowEntity = kNullEntity;
  private: Entity greenEntity  = kNullEntity;

  private: math::Pose3d redOn    {5.64, 0, 5.6, 0, 0, 0};
  private: math::Pose3d yellowOn {5.64, 0, 5.0, 0, 0, 0};
  private: math::Pose3d greenOn  {5.64, 0, 4.4, 0, 0, 0};
  private: math::Pose3d hidePos  {5.64, 0, -100, 0, 0, 0};

public:
  void PostUpdate(const UpdateInfo &_info,
                  const EntityComponentManager &_ecm) override
  {
    if (_info.paused) return;

    double now = std::chrono::duration<double>(_info.simTime).count();

    // Find entities every time until found
    if (redEntity == kNullEntity || yellowEntity == kNullEntity || greenEntity == kNullEntity)
    {
      _ecm.Each<components::Model, components::Name>(
        [&](const Entity &_entity,
            const components::Model *,
            const components::Name *_name) -> bool
        {
          std::string n = _name->Data();
          if (n == "red_light_model")    redEntity    = _entity;
          if (n == "yellow_light_model") yellowEntity = _entity;
          if (n == "green_light_model")  greenEntity  = _entity;
          return true;
        });
      return;
    }

    if (!initialized && now > 0.0)
    {
      initialized    = true;
      phaseStartTime = now;
      currentPhase   = RED;
      ShowPhase(const_cast<EntityComponentManager &>(_ecm), RED);
      std::cout << "[TL] Init -> RED at t=" << now << std::endl;
      return;
    }

    if (!initialized) return;

    double elapsed  = now - phaseStartTime;
    double duration = (currentPhase == RED)    ? redDuration :
                      (currentPhase == GREEN)  ? greenDuration :
                                                 yellowDuration;

    if (elapsed >= duration)
    {
      if      (currentPhase == RED)    currentPhase = GREEN;
      else if (currentPhase == GREEN)  currentPhase = YELLOW;
      else if (currentPhase == YELLOW) currentPhase = RED;

      phaseStartTime = now;
      ShowPhase(const_cast<EntityComponentManager &>(_ecm), currentPhase);

      std::cout << "[TL] t=" << now << " -> "
                << (currentPhase == RED    ? "RED" :
                    currentPhase == GREEN  ? "GREEN" : "YELLOW")
                << std::endl;
    }
  }

private:
  // Explicitly show ONE light and hide the other TWO
  void ShowPhase(EntityComponentManager &_ecm, Phase phase)
  {
    MoveTo(_ecm, redEntity,    phase == RED    ? redOn    : hidePos);
    MoveTo(_ecm, yellowEntity, phase == YELLOW ? yellowOn : hidePos);
    MoveTo(_ecm, greenEntity,  phase == GREEN  ? greenOn  : hidePos);
  }

  void MoveTo(EntityComponentManager &_ecm,
              Entity _entity,
              const math::Pose3d &_pose)
  {
    if (_entity == kNullEntity) return;
    auto *comp = _ecm.Component<components::Pose>(_entity);
    if (comp)
    {
      comp->Data() = _pose;
      _ecm.SetChanged(_entity,
                      components::Pose::typeId,
                      ComponentState::OneTimeChange);
    }
    else
    {
      _ecm.CreateComponent(_entity, components::Pose(_pose));
    }
  }
};

GZ_ADD_PLUGIN(TrafficLightPlugin,
              System,
              ISystemPostUpdate)
